import express from "express";
import helmet from "helmet";
import cookieParser from "cookie-parser";
import rateLimit from "express-rate-limit";
import crypto from "node:crypto";
import mongoose from "mongoose";
import { buildSchema, parse, validate, execute, visit } from "graphql";
import { Dataset, Comparison } from "./db.js";
import { analyze, scenario } from "./analysis.js";

const schema = buildSchema(`
  scalar JSON
  input Filters {state:String sector:String sex:String age:String}
  type Dataset {id:ID! period:String! payload:JSON! hashes:JSON!}
  type Summary {adults:Float! capable:Float! excluded:Float! sample:Float! rate:Float suppressed:Boolean!}
  type StateSummary {state:String! adults:Float! capable:Float! excluded:Float! sample:Float! rate:Float suppressed:Boolean! review:String!}
  type AgeSummary {age:String! rate:Float sample:Float! suppressed:Boolean!}
  type Analysis {filters:JSON! adults:Float! capable:Float! excluded:Float! sample:Float! rate:Float suppressed:Boolean! states:[StateSummary!]! ages:[AgeSummary!]!}
  type Scenario {baseline:Float share:Float! newlyCapable:Float sample:Float! suppressed:Boolean!}
  type Comparison {id:ID! title:String! note:String! datasetId:ID! filters:JSON! summary:JSON! createdAt:String!}
  type Query {dataset(version:ID):Dataset! analysis(version:ID,filters:Filters):Analysis! scenario(version:ID,filters:Filters,share:Float!):Scenario! comparisons:[Comparison!]!}
  type Mutation {saveComparison(version:ID!,title:String!,note:String!,filters:Filters!):Comparison! deleteComparison(id:ID!):Boolean!}
`);

export function createApp({
  activeVersion,
  dev = false,
  origin = process.env.APP_ORIGIN || process.env.RENDER_EXTERNAL_URL,
} = {}) {
  const app = express();
  app.disable("x-powered-by");
  const proxyHops = Number(process.env.TRUST_PROXY_HOPS || 0);
  if (!Number.isInteger(proxyHops) || proxyHops < 0 || proxyHops > 5)
    throw new Error("Invalid TRUST_PROXY_HOPS");
  if (proxyHops) app.set("trust proxy", proxyHops);
  if (process.env.NODE_ENV === "production" && !origin?.startsWith("https://"))
    throw new Error("Set APP_ORIGIN to the public HTTPS origin");
  app.use(
    helmet({
      contentSecurityPolicy: dev
        ? false
        : {
            directives: {
              "script-src": ["'self'"],
              "style-src": ["'self'", "'unsafe-inline'"],
              "img-src": ["'self'", "data:"],
            },
          },
    }),
  );
  app.use(express.json({ limit: "32kb" }), cookieParser());
  app.get("/healthz", (req, res) =>
    res
      .status(mongoose.connection.readyState === 1 ? 200 : 503)
      .json({
        status: mongoose.connection.readyState === 1 ? "ready" : "unavailable",
      }),
  );
  app.use(
    "/graphql",
    rateLimit({
      windowMs: 60000,
      limit: 180,
      standardHeaders: "draft-8",
      legacyHeaders: false,
      message: {
        errors: [
          { message: "Too many requests. Please wait a minute and try again." },
        ],
      },
    }),
  );
  app.post("/graphql", async (req, res) => {
    // Same-origin JSON only; cookies never authenticate cross-origin writes.
    const expected = origin || `${req.protocol}://${req.get("host")}`;
    if (req.get("origin") && req.get("origin") !== expected)
      return res
        .status(403)
        .json({ errors: [{ message: "Cross-origin request rejected" }] });
    if (!req.is("application/json"))
      return res
        .status(415)
        .json({ errors: [{ message: "Send application/json" }] });
    let token = req.cookies.upi_session;
    if (!/^[a-f0-9]{64}$/.test(token || "")) {
      token = crypto.randomBytes(32).toString("hex");
      res.cookie("upi_session", token, {
        httpOnly: true,
        sameSite: "strict",
        secure: process.env.NODE_ENV === "production",
        maxAge: 1000 * 60 * 60 * 24 * 30,
        path: "/",
      });
    }
    const owner = crypto.createHash("sha256").update(token).digest("hex");
    const getData = async (version) => {
      const row = await Dataset.findOne({
        id: version || activeVersion,
      }).lean();
      if (!row) throw new Error("Dataset version not found");
      return row;
    };
    const output = (r) => ({
      ...r,
      id: r._id.toString(),
      createdAt: new Date(r.createdAt).toISOString(),
    });
    const root = {
      dataset: ({ version }) => getData(version),
      analysis: async ({ version, filters }) =>
        analyze((await getData(version)).payload, filters),
      scenario: async ({ version, filters, share }) =>
        scenario((await getData(version)).payload, filters, share),
      comparisons: async () =>
        (
          await Comparison.find({ owner })
            .sort({ createdAt: -1 })
            .limit(50)
            .lean()
        ).map(output),
      saveComparison: async ({ version, title, note, filters }) => {
        if (!title.trim() || title.length > 100 || note.length > 2000)
          throw new Error(
            "Use a title of 1–100 characters and a note of at most 2,000 characters",
          );
        if ((await Comparison.countDocuments({ owner })) >= 50)
          throw new Error("Limit of 50 saved comparisons reached");
        const data = await getData(version),
          result = analyze(data.payload, filters);
        const row = await Comparison.create({
          owner,
          datasetId: data.id,
          title: title.trim(),
          note,
          filters: result.filters,
          summary: {
            adults: result.adults,
            capable: result.capable,
            excluded: result.excluded,
            sample: result.sample,
            rate: result.rate,
            suppressed: result.suppressed,
          },
        });
        return output(row.toObject());
      },
      deleteComparison: async ({ id }) => {
        if (!mongoose.isValidObjectId(id))
          throw new Error("Invalid comparison ID");
        return (
          (await Comparison.deleteOne({ _id: id, owner })).deletedCount === 1
        );
      },
    };
    try {
      const { query, variables, operationName } = req.body || {};
      if (typeof query !== "string" || query.length > 12000)
        throw new Error("Invalid query");
      const document = parse(query);
      let fields = 0,
        depth = 0,
        maxDepth = 0,
        fragments = false;
      visit(document, {
        Field: {
          enter() {
            fields++;
            maxDepth = Math.max(maxDepth, ++depth);
          },
          leave() {
            depth--;
          },
        },
        FragmentSpread() {
          fragments = true;
        },
      });
      if (fields > 120 || maxDepth > 8 || fragments)
        throw new Error("Query is too complex");
      const errors = validate(schema, document);
      if (errors.length)
        return res
          .status(400)
          .json({ errors: errors.map((e) => ({ message: e.message })) });
      const result = await execute({
        schema,
        document,
        rootValue: root,
        variableValues: variables,
        operationName,
      });
      // Keep infrastructure details out of GraphQL responses.
      if (result.errors)
        result.errors = result.errors.map((e) => ({
          message: /Mongo|ECONN|server selection/i.test(e.message)
            ? "Database unavailable; please retry."
            : e.message,
        }));
      res.set("Cache-Control", "no-store").json(result);
    } catch (error) {
      res.status(400).json({ errors: [{ message: error.message }] });
    }
  });
  app.use((err, req, res, next) =>
    res.status(err.status || 500).json({
      errors: [
        {
          message:
            err.status === 413
              ? "Request too large"
              : "Request could not be processed",
        },
      ],
    }),
  );
  return app;
}
