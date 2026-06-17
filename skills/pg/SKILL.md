---
name: pg
description: "PG (PPR/Gantree) — AI-native intent specification notation. Gantree for hierarchical structure decomposition, PPR for detailed logic with AI_ cognitive functions, → pipelines, and [parallel] blocks. This skill is the notation reference that enables AI to comprehend and execute PG-written documents. Auto-load when encountering Gantree trees, PPR def blocks, AI_ prefixed functions, → pipelines, or any skill/document written in PG notation."
user-invocable: false
disable-model-invocation: false
---

# PG — PPR/Gantree Notation v1.3

> **A DSL with AI as its runtime.**
> Deterministic logic is written in Python; AI cognitive operations are denoted with the `AI_` prefix.
> Together they form a single program — the AI reads it and performs the entire task.

PG denotes all of an AI's actions (judgment, reasoning, recognition, creation) at the programming level and makes them executable by an AI runtime. Gantree decomposes structure, and PPR specifies the semantics of each component. It is a communication language between humans and AI, and between AI and AI; a document written in PG is simultaneously a design specification, an execution intent, and a communication medium.

## Quick Start

1. Decompose the task hierarchically with **Gantree** (indentation = hierarchy)
2. Describe detailed logic only for complex nodes using **PPR `def`** blocks
3. Use the **`AI_`** prefix where AI judgment is needed, and real code for exact computation
4. Embed completion conditions with **`acceptance_criteria`**
5. Execute → verify → rework if needed

```
MyTask // task description (in-progress)
    StepA // first step (done)
    StepB // second step (in-progress) @dep:StepA
        # input: data from StepA
        # process: AI_analyze(data) → result
        # criteria: accuracy >= 0.9
```

That is all of PG. Detailed definitions follow below.

---

## Core Properties

### Parser-Free Property

PG's most important architectural property: **no parser, compiler, or runtime toolchain is required.**

- A PG document is composed of notation the AI already understands (Python syntax, indentation hierarchy, function composition)
- The AI does not parse a PG document — it **comprehends** it
- A single PG document fulfills 5 roles simultaneously: design specification, implementation intent, AI execution command, communication medium, organizational contract

### Co-evolutionary Property

A co-evolutionary property whereby advances in the AI runtime directly translate into higher PG execution quality.

- As AI models improve, a PG document produces better results **without modification**
- Conversely, refining a PG specification raises the execution accuracy of the same AI
- PG can analyze, design, and verify itself (self-reference)

### DL/OCME Paradigm

PG is the first implementation of the DL/OCME (Define Language / Optimized Code for Machine Engineering) paradigm.

- Unlike the 70-year PL/SE paradigm (targeting deterministic machines), it presupposes an AI cognitive runtime as the execution target
- The non-deterministic output of an `AI_` function is not a bug but a **design asset**

### AI-to-AI Communication Layer

PG is designed as the **primary communication layer** for AI-to-AI communication.

- In AI-to-AI communication, natural language is **not** the core execution language
- Natural language is used only as supplementary metadata when needed (`//` comments, `"""docstring"""`)
- Intent, structure, procedure, status, and verification are **conveyed directly** by PG syntax (`AI_`, `→`, `@dep:`, `[parallel]`, `acceptance_criteria`)
- Cross-model compatibility: any AI model understands PG immediately (demonstrated on Claude, Kimi, ChatGPT, Gemini, etc.)

### Limitations of Existing Notations and PG's Solution

| Existing limitation | PG's solution |
|----------|----------|
| No way to denote AI capabilities at the programming level | **PPR** — specifies cognitive operations at the function-signature level via `AI_` functions |
| No notation to track progress status in the tree | **Gantree status codes** — 6 stages such as `(done)/(in-progress)/(designing)` |
| Visualization collapses as the tree grows | **`(decomposed)`** — maximum allowed depth of 5 levels; split upon entering level 6 |
| Loss of connectivity between split nodes | **`@dep:`, `→`, decomposed-tree references** preserve connectivity |

---

## Gantree — Hierarchical Structure

Decompose the system into an indentation-based tree.

### Node Syntax

```
NodeName // description (status) [@v:version] [@dep:dependency] [#tag]
```

- **NodeName**: CamelCase identifier
- **// description**: natural-language description
- **(status)**: `done` | `in-progress` | `designing` | `blocked` | `decomposed` | `needs-verify`
- **@v:X.Y**: version (used on the root node)
- **@dep:A,B**: execute after A and B are complete
- **#tag**: classification tag (optional, for search/filter)
- **[parallel]...[/parallel]**: parallel execution section

### Status Code Execution Rules

| Status | AI execution rule |
|--------|-------------|
| `(done)` | already complete — skip |
| `(in-progress)` | execute the PPR def block |
| `(designing)` | stub / basic logic only |
| `(blocked)` | skip |
| `(decomposed)` | reference the split tree |
| `(needs-verify)` | perform verification after execution → on pass `(done)`, if rework needed `(designing)`, if unrecoverable `(blocked)` |

### Structural Rules

- 4 spaces = 1 level (no tabs)
- Maximum allowed depth of 5 levels; upon entering level 6 → split with `(decomposed)`
- 10+ children → branching needed
- `[parallel]` blocks may not be nested (flat parallelism only)
- `@dep:` between nodes inside a `[parallel]` block is forbidden (parallel = independent execution)

### `(decomposed)` Split Example

Upon entering depth level 6, split into a separate tree and reference it from the original:

```
OrderSystem // order system (in-progress)
    PaymentFlow // payment flow — see PaymentFlow tree (decomposed)
    ShippingFlow // shipping flow (designing)

PaymentFlow // split payment detail tree (in-progress)
    ValidateCard // card validation (done)
    ChargeCard // card charge (in-progress) @dep:ValidateCard
    SendReceipt // receipt dispatch (designing) @dep:ChargeCard
```

When splitting files: mark `(decomposed)` in the original DESIGN, and put the detail tree in a separate section or a separate `.md` file.

### Example

```
PaymentSystem // payment system (in-progress) @v:1.0
    UserDB // user DB connection (done)
    Auth // authentication (done) @dep:UserDB
    [parallel]
    ValidateCard // card validation (done)
    CheckBalance // balance check (done)
    [/parallel]
    ProcessPayment // payment processing (designing) @dep:ValidateCard,CheckBalance
```

### Atomic Node

Diagnostic heuristics (high likelihood of being atomizable when 5 or more are satisfied):

1. **I/O clarity** — expressible as a function signature
2. **Single responsibility** — describable in one sentence without "AND"
3. **Implementation complexity** — completable as a single function (note: 50 lines or fewer is typical)
4. **Time predictability** — AI can write complete code within 15 minutes
5. **Re-decomposition pointless** — further decomposition would be excessive granularity
6. **Independent execution** — external dependencies ≤ 2
7. **Domain independence** — understandable with only basic knowledge

> **Final decision rule (15-minute rule)**: The 7 heuristics above are diagnostic tools, and the **15-minute rule has final authority**. Even if 5 heuristics are satisfied, if it cannot be completed within 15 minutes → decompose further. Even if only 4 heuristics are satisfied, if it can be completed within 15 minutes → atomic node.

---

## PPR — Detailed Logic

An intent specification the AI understands. Denotes cognitive operations based on Python syntax.

### Data Type Notation

Based on Python type-hint syntax, but **relaxed notation is allowed to convey intent**. The goal is not strict Python typing compatibility but for the AI to understand the I/O structure.

```python
text: str                                          # basic type
user: dict = {"name": str, "age": int}             # schema literal (non-standard Python, allowed in PG)
status: Literal["draft", "review", "published"]    # enumeration
nickname: Optional[str]                            # optional
Section = dict[str, str | list[str] | int]         # type alias
```

### Differences from Python (only 5)

| Notation | Meaning |
|------|------|
| `AI_` prefix | declares an AI cognitive operation |
| `→` | data pipeline (left→right flow) |
| `[parallel]` | parallel execution section |
| relaxed types | for conveying intent (strictness not required) |
| omitted imports | infrastructure setup may be omitted |

### AI_ Functions

```python
def AI_[verb]_[target](params: Type) -> ReturnType:
    """intent description"""
```

4 cognitive categories:

```python
# Judgment
score: float = AI_assess_quality(text, domain)

# Reasoning
plan: list = AI_generate_plan(goal, constraints)

# Recognition
intent: str = AI_understand_intent(query)

# Creation
content: str = AI_generate_content(brief, style)
```

### AI_make_ Causative Pattern

The `AI_` prefix is an **intransitive** expression in which the AI performs cognition directly. However, when the AI **induces** a change in a target, the `AI_make_` causative pattern is used.

`AI_make_` is **not** a separate fifth cognitive category — each of the 4 categories (judgment/reasoning/recognition/creation) has a causative variant.

```python
# AI_ — intransitive: the AI performs directly
keywords = AI_extract(text)             # the AI extracts
score = AI_assess(quality)              # the AI assesses

# AI_make_ — causative: the AI makes the target do something
evolved = AI_make_evolve(system)        # makes the system evolve
adapted = AI_make_adapt(behavior, ctx)  # makes the behavior adapt
converged = AI_make_converge(opinions)  # makes the opinions converge
differentiated = AI_make_differentiate(cell, env)  # makes the cell differentiate
```

**Decision order** (when ambiguous):
1. Is the subject of the verb the AI itself? → `AI_`
2. Does the object (target) of the verb change its own state? → `AI_make_`
3. Cannot decide → use `AI_` (conservative default)

```python
# the AI analyzes (the AI is the subject)
analysis = AI_analyze(data)

# the AI makes the system self-learn (the system is the agent of change)
learned_system = AI_make_learn(system, feedback)

# the AI makes the agents reach agreement (the agents are the agents of change)
consensus = AI_make_agree(agents, proposal)
```

**The `AI_` prefix system is not an absolute rule but an evolvable system.** As AI models' cognitive abilities expand, new prefix patterns may naturally emerge. This is PG's Co-evolutionary Property.

**Rule**: use real code for precise computation, and `AI_` only where AI judgment is needed.

```python
# ❌ using AI_ where accuracy is required
result = AI_calculate(2 + 2)
formatted = AI_format_date("2024-01-01")

# ✅ use real code
result = 2 + 2

# ✅ use AI_ where AI judgment is needed
analysis: dict = AI_analyze_trend(sales_data: list[float])
```

### → Pipeline

```python
# basic: left output is the right input
raw → AI_clean → AI_extract → AI_classify → result

# branching
input → {
    "sentiment": AI_analyze_sentiment → score,
    "keywords": AI_extract_keywords → words,
}

# merging: combine multiple results into one
[parallel]
tech = AI_analyze(data, lens="tech")
market = AI_analyze(data, lens="market")
[/parallel]
synthesis = AI_synthesize(tech, market) → result
```

**Error propagation rule**: when a pipeline stage fails (None/exception), the **entire pipeline halts** and returns the output of the last successful stage. To ignore a failed stage and continue, you must explicitly wrap it with Python `try/except`.

```python
# basic: pipeline halts on stage failure
raw → AI_clean → AI_extract → result
# AI_clean fails → pipeline halts, returns raw

# explicit error tolerance: wrap with try/except
try:
    result = raw → AI_clean → AI_extract → AI_classify
except:
    result = AI_generate_fallback(raw)
```

### Convergence Loop — AI Self-Improvement Iteration

```python
draft = AI_generate(brief)
while True:
    eval = AI_evaluate(draft, criteria)
    if eval.score >= threshold:
        break
    draft = AI_revise(draft, eval.feedback)
```

Key: the AI evaluates its own output and iterates on improvement if it falls below the criteria.

### Failure Strategy — Self-Correction on Failure

```python
for attempt in range(max_retry):
    result = AI_execute(task)
    if AI_verify(result, acceptance_criteria):
        return result  # success
    if attempt >= 1:
        task.ppr = AI_redesign(task, result.failure_reason,
                               constraint='preserve_public_interface')
task.status = "blocked"  # final failure
```

Key: the AI can redesign the internal implementation while preserving the public interface.

### acceptance_criteria — Embedded Verification Criteria

```python
def some_task(input: InputType) -> OutputType:
    """task description"""
    # acceptance_criteria:
    #   - all fields included
    #   - AI_assess_quality >= 0.85
    #   - response time < 5s
```

3 types: **functional** (output satisfied) | **qualitative** (AI judgment) | **structural** (format compliance)

### Flow Control

Use Python flow-control syntax as is.

```python
# conditional branching
language = AI_detect_language(input_text)
if language == "ko":
    result = AI_process_korean(input_text)
else:
    result = AI_translate_to_korean(input_text)

# exception handling
try:
    response = call_external_api(query)
except APIError as e:
    fallback = AI_generate_fallback_response(query, error=str(e))
```

---

## Gantree ↔ PPR Linkage

| Node type | PPR linkage method | Suitable scale |
|----------|-------------|----------|
| simple atom | inline — write `AI_extract_keywords` directly | single call |
| brief PPR | describe 3-7 lines of logic in `#` comments under the node | small (has flow but no def needed) |
| separate def block | full PPR function definition | medium or larger (conditions/loops/types needed) |

**Recommended keys for brief PPR** (optional — a recommended style, not mandatory):

- `# input:` — input data/type
- `# process:` — processing logic
- `# output:` — output result
- `# criteria:` — completion condition

```
# Gantree — 3-tier expression
TopicAnalyzer // topic analysis (done)         ← separate PPR def (complex)
    AI_extract_keywords // keywords (done)      ← inline (simple)
    AI_classify_topic // classification (done)  ← inline (simple)

DataCleaner // data cleaning (done)            ← brief PPR (medium)
    # input: raw_data: list[dict]
    # filtered = [d for d in raw_data if d["status"] != "deleted"]
    # cleaned = AI_normalize_fields(filtered)
    # return cleaned
```

```python
# PPR def block — for complex nodes
def topic_analyzer(text: str, domain: Optional[str] = None) -> dict:
    keywords = AI_extract_keywords(text)
    if domain:
        keywords = [k for k in keywords if is_in_domain(k, domain)]
    category = AI_classify_topic(text, hint_keywords=keywords)
    return {"keywords": keywords, "category": category}
```

---

## Progressive Formalization — 3-Level Progressive Formalization

PG is **progressively formalized** from natural language up to a complete formal specification. The user need not know PG syntax from the start.

| Level | Form | Suitable task | PG file creation |
|---|---|---|---|
| **Level 1** | one line of natural language | bug fix, config change (≤3 nodes) | none (inline execution) |
| **Level 2** | Gantree + `#` comments | feature addition, refactoring (4~10 nodes) | optional |
| **Level 3** | Gantree + PPR `def` + `acceptance_criteria` | system design, large-scale implementation (10+ nodes) | required |

```python
# Level 1: execute with natural language alone — no PG syntax needed
"Fix clippy warnings in ocwr_daemon"

# Level 2: Gantree + inline comments — capture structure only
FixClippy // fix clippy warnings (in-progress)
    DaemonCrate // ocwr_daemon (designing)
        # cargo clippy → warning list → fix
    GatewayCrate // ocwr_gateway (designing)

# Level 3: complete PG specification — large-scale task
def fix_clippy(workspace: Path) -> FixResult:
    """remove clippy warnings across the whole workspace"""
    # acceptance_criteria:
    #   - cargo clippy --workspace -- -D warnings → 0 warnings
```

### Automatic Promotion

When complexity increases during execution, the AI automatically promotes to a higher level:
- More than 3 subtasks discovered during Level 1 execution → promote to Level 2
- Verification criteria needed during Level 2 execution → promote to Level 3
- **On promotion, the status of already-completed work is preserved**

## 3-Stage Development Process

1. **Gantree structure design** — Top-Down BFS hierarchical decomposition → down to atomic nodes
2. **PPR detailing and execution** — describe each node as a `def` block, execute/skip according to status
3. **Self cross-verification** — review from 3 perspectives: **consistency** (no internal contradictions), **completeness** (no omissions), **correctness** (specification matches execution)

---

## When You Encounter a Document Written in PG

1. Gantree tree → grasp the hierarchy and execution order
2. `(status)` → decide execute/skip
3. `@dep:` → determine dependency order
4. `[parallel]` → parallel processing
5. if a PPR `def` is present → interpret and execute
6. if a `#` brief PPR is present → interpret the inline comments and execute
7. if `AI_` inline → execute directly
8. if nothing is present → recurse into child nodes

---

## Checklist

### Gantree Design

- [ ] Is every node within 5 levels?
- [ ] Is each node's status clearly indicated?
- [ ] Is it sufficiently decomposed down to atomic nodes?
- [ ] Are node names consistently CamelCase?
- [ ] Are `@dep:` dependencies indicated where needed?
- [ ] Are there no circular `@dep:` references? (verify by topological sort: no cycle if all nodes can be sorted)
- [ ] Are `[parallel]`-capable areas identified?
- [ ] Is it output with 4-space indentation inside a code block?

### PPR Detailing

- [ ] Is a PPR `def` block written for complex nodes?
- [ ] Are I/O specified with Python type hints?
- [ ] Does flow control follow Python syntax?
- [ ] Are `AI_` functions snake_case with return types specified?
- [ ] Is the `AI_make_` prefix used for causative meaning (making a target do something)?
- [ ] Is deterministic logic written in real code?

### Common Mistakes

| Mistake | Solution |
|------|--------|
| Writing only Gantree, omitting PPR | Complex nodes must have a PPR `def` block |
| Trying to express all logic in the tree | Separate flow control/types into PPR |
| Exceeding maximum depth of 5 levels (entering level 6) | Split into a separate tree with `(decomposed)` |
| 10 or more child nodes | Add an intermediate group node |
| Using `AI_` where accuracy is required | Use real code for math/conversion |
| Undefined I/O types | Declare with Python type hints |

---

## Reference — Execution Guides (Leveraging the Essence)

> Where SKILL.md *defines* the notation, the documents below provide procedures for **programming the work process itself** with that notation.
> Load `{SKILL_DIR}/reference/<name>.md` as needed.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/work-as-program.md` | "programming the work itself with pg" — 7-stage loop (analyze→design→work design→**PPR simulation pre-verification**→execute→redesign→checkpoint) |
| `{SKILL_DIR}/reference/control-flow-cookbook.md` | type I/O · conditions · branching · loops · contracting (factory line) patterns — orchestrating complex multi-stage tasks |
