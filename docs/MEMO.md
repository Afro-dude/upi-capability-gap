# What the survey supports about India's UPI capability gap

The January–March 2025 CMS-T microdata estimates that 48.6% of persons aged 15+
report UPI capability. The weighted estimate of those not capable is 46.9 crore.
These are survey point estimates, not counts of inactive UPI accounts.

Among recent internet users, 69.55% report online-banking capability. About
19.5 crore recent users report being unable to transact online. The numerator
and denominator are calculated on the same respondents. Internet use does not
imply smartphone ownership, equal access quality, or equal financial resources.

Capability differs across age, sex and rural/urban groups. These patterns can
motivate further investigation, but do not identify why the gaps arise or which
intervention is most effective. The household internet-barrier responses refer
to home internet, not directly to UPI. They do not establish that infrastructure
or affordability policies should be deprioritised.

State-level survey comparisons have a stronger basis than complete-volume
transaction rankings. Geography is encoded in NSS-Region. An official-table
check reproduces 35/36 online-banking rates to published precision. Himachal
Pradesh remains unresolved (64.4% from supplied data versus 66.2% in the report).
Its figures are flagged, not corrected by assumption. Sampling uncertainty is
not quantified, so close rankings should not be used to claim meaningful gaps.

NPCI records 38.1% of this quarter's volume without state attribution. The
observed classified volume can be displayed alongside capability, but the
remaining volume may be distributed differently across states. Simple
allocation rules preserve rankings by construction; this does not validate
complete-volume rankings. Regression residuals cannot diagnose merchant-side
constraints or justify withdrawing capability programmes from particular states.

## Practical next steps

1. Resolve the HP discrepancy with the data publisher or a documented revised
   release. Do not change survey responses or weights to force a match.
2. Obtain frame/listing metadata for the official variance calculation before
   publishing confidence intervals or significance rankings.
3. If intervention planning is the aim, collect intervention outcomes and
   measures such as account access and merchant acceptance using compatible
   geography. Treat proposed mechanisms as hypotheses to test.
4. Build the web product around capability exploration, source transparency and
   saved comparisons. A what-if population calculator may use user-specified
   assumptions, but should not promise adoption or transaction growth.

The earlier memo's transaction ceiling, policy prioritisation and causal
interpretations have been superseded by this document. See `DATA_NOTES.md` for
definitions and `AUDIT.md` for verification details.
