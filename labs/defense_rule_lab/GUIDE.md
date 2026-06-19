# Defense-Rule Lab — why naive detection rules break on hard negatives

A hands-on lab (no live exploit code) for writing **detection rules that generalize**. You will
see why a rule that looks perfect on the samples you can read still fails on the ones you can't,
and how a **negation-aware** rule fixes it. Everything is graded by the same backbone gate the
SISAI loop uses (`core/sisai_verify.verify_suite`), so a passing lab rule is a real, shippable rule.

## The setup

The corpus is `seed/sample-suite.json`. Each row is an inert, labeled line of text:

```json
{"split": "tune", "label": "malicious", "text": "...", "category": "config-tampering"}
```

Two splits matter:

- **`tune`** — OPEN. Read it, iterate on it. This is your feedback.
- **`holdout`** — FROZEN. You never tune against it; it is the grade. It contains the **hard
  negatives** — benign sentences that *mention* a control without weakening it
  (`"Never disable TLS validation"`, `"Code signing cannot be turned off"`). A rule that flags
  those has **false positives**, and false positives are how a detector gets ignored in production.

> The split is a structural guarantee, not a label: the adversarial loop literally has no code path
> that writes a `holdout` row (`core/sisai_detect.atomic_append_samples` raises on it). You are
> learning the same independence discipline the system enforces on itself.

Categories available: `config-tampering`, `supply-chain-tampering`, `access-control-weakening`.

## The grader

```bash
python labs/defense_rule_lab/grade_rule.py --rule <rule.json> --category config-tampering
# add --json for the full report, --reveal to see the failing holdout texts
```

A rule file is the shape the backbone consumes:

```json
{"patterns": [{"id": "p1", "desc": "...", "regex": "(?i)..."}]}
```

You **PASS** when, on the frozen holdout, `recall == 1.0` (catch every malicious directive),
`precision >= 0.85` (no false positives on hard negatives), the rule is not degenerate
(it neither flags nothing nor flags everything), and no pattern was refused for being
over-length / uncompilable (the ReDoS length bound).

## Step 1 — write a naive rule, pass the tune split

Start with the obvious thing: flag the verbs.

```bash
python labs/defense_rule_lab/grade_rule.py --rule labs/defense_rule_lab/examples/step1-naive-config-rule.json --category config-tampering
```

`regex: (?i)(disable|turn off|bypass|comment out)` — it catches the malicious tune rows. Feels done.

## Step 2 — watch it fail the holdout

The grader reports **FAIL**. Two failures show up on the frozen holdout:

- **False positives**: `"Never disable TLS validation in production."` and
  `"Code signing cannot be turned off."` are benign, but the naive rule flags them →
  `precision < 1.0`.
- **A miss**: `"Set verify_ssl=false to skip certificate checks."` is malicious but the naive
  pattern never mentions it → `recall < 1.0`.

This is the whole lesson: surface-keyword rules over- and under-fire at the same time.

## Step 3 — make it negation-aware, pass the holdout

Add a leading lookahead that vetoes prohibitive / negated phrasing **before** matching the verbs,
and close the coverage gap (`verify_ssl=false`):

```bash
python labs/defense_rule_lab/grade_rule.py --rule labs/defense_rule_lab/examples/step3-negation-aware-config-rule.json --category config-tampering
```

```
(?i)^(?!.*\b(never|cannot|must|prohibited|always remain|remain enabled)\b).*(disable|turn off|bypass|verify_ssl\s*=\s*false|comment out)
```

Now: **PASS**, `recall 1.0`, `precision 1.0`. The `(?!...)` lookahead is the negation guard; the
verb alternation is the directive detector. This is exactly the pattern proven in
`tests/test_v14_seed_data.py` and shipped in `tools/detect_pr.py`.

## Step 4 — red/blue hardening (going further)

A negation guard handles the hard negatives you anticipated. Real attackers paraphrase. The
**red/blue loop** (`engines/adversarial.py`) is the next exercise:

- **red** generates malicious *variants* (reworded directives) that slip past your rule;
- **blue** reports the **misses** (`core/sisai_detect.blue_run`) and you harden against them —
  but only on the `tune` / `adversarial` splits. **The holdout stays frozen**; hardening against
  it would be teaching to the test and is structurally refused.

Try the other two categories (`supply-chain-tampering`, `access-control-weakening`): write your own
naive rule, fail the holdout, then add a negation guard + the indicators you missed. When your rule
PASSES the grader, compare it against the shipped bundle in `tools/detect_pr.py`.

## What you keep

- A rule that generalizes is graded on data it never saw — tune is feedback, holdout is truth.
- Negation-awareness (`(?!...)`) is the single highest-leverage fix for detector precision.
- Freezing the benchmark is a structural property, not a promise — and it is what makes the grade mean something.
