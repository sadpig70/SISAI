# Semantic-judge verdicts — inbox

Per-row semantic verdicts from external SEMANTIC JUDGES, one file per (category, judge):
`<category>/<judge_model>.json`, ingested via
`python calibration/semantic_ingest.py --ingest <submission.json>`.

A judge classifies each holdout row by MEANING, **blind to the labels and the detector rules**, and
**must differ from both the rule author and the holdout's curator** (3-way distinct; the curator knows
the labels). Multiple judges per category → majority vote. See
`docs/INDEPENDENT-CURATION-PROTOCOL.md` (Semantic-judge TaskSpec). Starts empty; entries appear only as
real judge submissions arrive.
