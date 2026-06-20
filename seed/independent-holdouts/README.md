# Independent holdouts — inbox

Drop curator-submitted holdouts here, one JSON file per category (`<category>.json`), via
`python calibration/independent_eval.py --ingest <submission.json>` (which validates then writes here).

These holdouts are curated by a runtime **distinct from the rule author** (the SISAI meta-layer), so a
detector clearing them is genuine **independent** validation — unlike the single-author holdouts in
`seed/sample-suite.json`. See `docs/INDEPENDENT-CURATION-PROTOCOL.md` for the curator TaskSpec and the
submission format. This directory starts empty; entries appear only as real submissions arrive.
