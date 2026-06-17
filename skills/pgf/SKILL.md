---
name: pgf
description: "PGF (PPR/Gantree Framework) — AI-native design/execution framework. Supports system architecture design, work planning, autonomous execution, idea discovery, and full creation cycles. Gantree hierarchical decomposition + PPR pseudo-code for AI-comprehensible specifications. Triggers: 설계해줘, 구조 설계, 작업 분해, 아키텍처, 모듈 분리, 작업 계획, WORKPLAN, 프로젝트 구조화, Gantree, PPR, PGF, 발견, 창조, design, plan, execute, discover, create"
user-invocable: true
argument-hint: "design|plan|execute|full-cycle|loop|discover|create [project-name|start|cancel|status]"
---

# PGF (PPR/Gantree Framework) v2.5

> PG가 프로그래밍 언어라면, PGF는 라이브러리다.
> PG로 자주 실행하는 유용한 패턴(설계, 실행, 검증, 발견, 창조 등)을 정규화한 것이다.

## PG 기반 의존성

**PGF는 PG(PPR/Gantree Notation)를 기반 언어로 사용한다.** PG의 핵심 속성(Parser-Free, Co-evolutionary, DL/OCME, AI_ 함수, → 파이프라인, [parallel], Gantree 노드 문법)은 PG 스킬에 정의되어 있으며, PGF는 이를 상속한다.

> **PG 표기법 참조**: PG 스킬을 로드하여 Gantree 노드 문법, PPR 구문(AI_/AI_make_ 접두사, → 파이프라인, [parallel], acceptance_criteria, Convergence Loop, Failure Strategy), 데이터 타입, 원자 노드 판단 기준을 확인할 것.

PGF가 PG 위에 추가하는 것:
- **실행 모드** — design, plan, execute, full-cycle, loop, discover, create, micro, delegate
- **WORKPLAN + POLICY** — 실행 계획과 정책 블록
- **status JSON** — 노드별 실행 상태 추적
- **Phase transition** — 모드 간 자동 전환 조건
- **Session Learning** — 세션 간 학습과 전략 적응
- **Epigenetic PPR** — 컨텍스트 적응 실행, extract-ppr.py 자동 통합
- **Runtime Continuation** — hook/heartbeat/manual 등 런타임별 adapter 기반 장기 실행 보호
- **Design Review** — 구현 전 3관점 사전 검증

---

## Current Project PGF State

To check the current PGF state, scan the project's `.pgf/` directory:
- List `*.md` and `*.json` files in `.pgf/`
- Read `status-*.json` for execution progress (`summary.done / summary.total`)
- Check `.pgf/runtime/pgf-loop-state.json` for active pgf-loop status. Runtime adapters may mirror this state elsewhere, but `.pgf/runtime/` is canonical.

---

## PGF Notation Extensions

PG defines the canonical Gantree node syntax and 6 base status codes (`done`, `in-progress`, `designing`, `blocked`, `decomposed`, `needs-verify`). PGF adds **3 delegation status codes** used in `delegate` mode and AI-to-AI handoffs:

| Status | Meaning | Execution Rule |
|---|---|---|
| `(delegated)` | Handed off to another agent | Skip — executing remotely |
| `(awaiting-return)` | Delegation sent, result pending | Poll or wait for callback |
| `(returned)` | Result received, integration pending | Validate + integrate result |

State transition: `(designing) → (delegated) → (awaiting-return) → (returned) → (done)` (or `(blocked)` on validation failure).

All other notation rules (5-level depth, `[parallel]`, `@dep:`, PPR `def` blocks, Convergence Loop, Failure Strategy, atomicity 15-minute rule) follow PG skill verbatim.

---

## Reference Document Guide

> **Path convention**: `{SKILL_DIR}` is a runtime-neutral placeholder denoting **this skill's root directory** (the directory containing `SKILL.md`). Every agent runtime (Claude Code, Kimi, Gemini, MCP, Agent SDK, etc.) substitutes it with the local path where the `pgf` skill is installed. Use `{SKILL_DIR}/...` for all internal references — never hard-code absolute paths or runtime-specific env vars.

Reference documents for this skill are located in the `{SKILL_DIR}` directory. Load the appropriate file with the Read tool depending on the execution mode and need.

### Base Notation (PG 스킬)

PG 표기법의 핵심 문법은 PG 스킬에 정의되어 있다. PGF 실행 시 PG 스킬이 자동 로드된다.

| Source | Content |
|--------|---------|
| **PG skill** (`PG/SKILL.md`) | Gantree 노드 문법, status codes, PPR 구문 (AI_/AI_make_, →, [parallel]), 데이터 타입, 원자 노드 판단, Convergence Loop, Failure Strategy, 체크리스트 |

> PG 스킬에 정의된 내용은 PGF의 모든 레퍼런스 문서에서 재정의하지 않는다. 중복 발견 시 PG 스킬이 정본(canonical source)이다.

### Always Reference

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/pgf-format.md` | PGF file format (DESIGN/WORKPLAN .md structure, naming conventions) |

### Execution Discipline & Playbooks (실행 규율 — 본질 활용)

> 모드가 *무엇을* 하는지는 아래 Phase별 reference가, **어떻게 실수 없이 수행하는가**는 이 3종이 준다.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/execution-discipline.md` | 실수 없이 끝내는 실행 규율 — 분해→영속(.pgf)→배치 게이트→status 재개, 증거기반 verify(GATE-EVIDENCE), 3관점, 결정론 경계 |
| `{SKILL_DIR}/reference/large-work-playbook.md` | 대규모(>30노드)·다파일 작업 — pgxf 인덱스 + 배치 마이그레이션 + 원자적 안전 치환(줄바꿈/개선분/상호참조 보존) |
| `{SKILL_DIR}/reference/integration-doctrine.md` | 통합/융합 판정 — select-or-integrate, fuse vs federate, idea-layer 메타 폐루프(닫혔으나 안 좁아지는 나선) |

### Design Phase (design mode)

> Gantree 노드 문법, PPR 구문(`AI_`/`→`/`[parallel]` 등), 데이터 타입, Convergence Loop, Failure Strategy, 원자 노드 판단(15분 룰), 기본 체크리스트는 **PG 스킬(canonical)**을 참조. PGF가 추가하는 표기/검사 항목은 아래 "PGF Notation Extensions"와 "PGF Execution Checklist" 섹션을 참조.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/analyze-reference.md` | design --analyze reverse engineering — codebase → auto-generate DESIGN |
| `{SKILL_DIR}/reference/design-review-reference.md` | 3-perspective design review — feasibility/risk/architecture pre-implementation validation |

### Execution Phase (plan / execute / loop mode)

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/workplan-reference.md` | WORKPLAN conversion, POLICY block, Loop algorithm, error recovery |
| `{SKILL_DIR}/loop/loop-reference.md` | Runtime-adapter loop engine — node selection, prompt composition, error recovery |
| `{SKILL_DIR}/reference/verify-reference.md` | 3-perspective cross-verification — acceptance/quality/architecture, rework rules |
| `{SKILL_DIR}/reference/cycle-reference.md` | full-cycle + create unified spec — DESIGN→PLAN→EXECUTE→VERIFY pipeline, optional DISCOVER prepend, rework regression, session resumption |
| `{SKILL_DIR}/reference/review-reference.md` | review mode — iterative analysis, prioritization, fix, re-verification |
| `{SKILL_DIR}/reference/evolve-reference.md` | evolve mode — self-evolution cycle, capability audit, stabilization detection |

### Discovery/Creation Phase (discover / create mode)

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/discovery/discovery-reference.md` | IdeaFirst 7-stage pipeline, Agent parallel execution, result integration |
| `{SKILL_DIR}/discovery/archive-discovery.py` | Discovery artifact date-based archive script |

> `create` mode (5-phase autonomous: DISCOVER + DESIGN→VERIFY) and `full-cycle` mode (4-phase) share the same pipeline spec — see `reference/cycle-reference.md` in the Execution Phase table above.

### Agent Communication & Delegation

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/agent-protocol.md` | PG 기반 에이전트 간 소통 규격 — TaskSpec 형식, 병렬 파견, 결과 통합 |
| `{SKILL_DIR}/reference/delegate-reference.md` | DELEGATE 모드 — AI-to-AI 핸드오프, authority bounds, delegation chain |
| `{SKILL_DIR}/reference/micro-reference.md` | MICRO 모드 — ≤10 노드 제로 오버헤드 실행, 자동 승격 |
| `{SKILL_DIR}/reference/session-learning-reference.md` | Session Learning — 세션 간 학습, 패턴 누적, 전략 적응 |

### Advanced Reference (as needed)

> **Future protocols** (vision, no current implementation): PGF-MCP (typed intent execution over MCP), PGF-A2A (typed subtree handoff between agents). Use the existing execution modes and `agent-protocol.md` TaskSpec for current AI-to-AI communication needs.

### Persona Agents (discover/create mode)

Discovery Engine's 14 personas are independently defined as agent files in `{SKILL_DIR}/agents/`:

| Agent | Cognitive Style | Domain | Horizon |
|-------|----------------|--------|---------|
| `pgf-persona-p1.md` — Disruptive Engineer | creative | technology | long |
| `pgf-persona-p2.md` — Cold-eyed Investor | analytical | market | short |
| `pgf-persona-p3.md` — Regulatory Architect | critical | policy | long |
| `pgf-persona-p4.md` — Connecting Scientist | intuitive | science | long |
| `pgf-persona-p5.md` — Field Operator | analytical | technology | short |
| `pgf-persona-p6.md` — Future Sociologist | intuitive | society | long |
| `pgf-persona-p7.md` — Contrarian Critic | critical | market | short |
| `pgf-persona-p8.md` — Convergence Architect | creative | science_technology | long |
| `pgf-persona-p9.md` — Practical Agency Ethicist | critical | ethics | long |
| `pgf-persona-p10.md` — Embodied UX Anthropologist | intuitive | human_experience | short |
| `pgf-persona-p11.md` — Adversarial Robustness Analyst | critical | security | short |
| `pgf-persona-p12.md` — Regenerative Systems Ecologist | intuitive | ecology | long |
| `pgf-persona-p13.md` — Historical Cycle Analyst | analytical | history | long |
| `pgf-persona-p14.md` — Mechanism Designer | creative | economics | long |

---

## Execution Modes

PGF supports the following execution modes via `$ARGUMENTS`.

**Invocation examples:** `/PGF design MyProject`, `/PGF full-cycle ChatApp`, `/PGF loop start`, `/PGF discover`, `/PGF create`

| Mode | Trigger | Action |
|------|---------|--------|
| `design` | "설계해줘", "구조 설계" | Gantree structure design + PPR detailing → generate DESIGN-{Name}.md |
| `design --analyze` | "분석해줘", "구조 분석" | (design의 하위 옵션) Reverse-engineer existing system into PGF → read code → extract Gantree + PPR |
| `plan` | "작업 계획", "WORKPLAN" | DESIGN → WORKPLAN conversion + POLICY configuration |
| `execute` | "실행해줘", "구현해줘" | Sequential node execution based on WORKPLAN |
| `full-cycle` | "전체 진행", "풀사이클" | Full process: design → plan → execute → verify. **Opt-in 게이트**: `--with-review[=N]` 플래그로 design 직후 review 삽입 (max N회 revise, 기본 N=1) |
| `loop` | "루프", "자동실행" | Automatic or guided node traversal/execution via runtime-adapter WORKPLAN |
| `discover` | "발견해줘", "아이디어" | IdeaFirst 7-stage × 14 personas → idea discovery |
| `create` | "창조해", "자율 창조" | **Full autonomous execution: discover → design → plan → execute → verify** |
| `micro` | "간단히", "빠르게" | Zero-overhead execution for ≤10 nodes — bypass WORKPLAN |
| `review` | "검토해", "리뷰해" | Iterative review & improvement — 기존 산출물 면밀 검토·수정·재검증 반복 |
| `evolve` | "진화해", "자기개선" | Self-evolution cycle — 능력 gap 발견·설계·구현·검증·기록 반복 |
| `delegate` | "위임해", "맡겨" | AI-to-AI task handoff with PG TaskSpec, authority bounds, delegation chain |

**$ARGUMENTS parsing rules:**
- `$ARGUMENTS[0]`: mode keyword
- `$ARGUMENTS[1:]`: project name or target description
- No mode keyword → infer from context (e.g., presence of files in `.pgf/` directory)
- Project name only → defaults to `design` mode

### File Path Rules

```text
<project-root>/
    .pgf/
        DESIGN-{Name}.md          # System design (Gantree + PPR)
        WORKPLAN-{Name}.md        # Executable work plan
        status-{Name}.json        # Execution state tracking
```

`{Name}` = CamelCase project/task name. Multiple tasks can coexist in the same `.pgf/`.

### Progress Reporting

```text
[PGF] ✓ NodeName (done) | 3/12 nodes done | next: NextNode
[PGF] ✗ NodeName (blocked) | blocker: reason | skip → NextNode
```

---

## Integrated Execution Process

> 아래 Step들은 **순차 프로세스가 아닌 독립 모드**다. 사용자 지시나 PGF 모드에 따라 필요한 것만 실행한다. full-cycle/create 모드만이 여러 Step을 순차 연결한다.

### Step 1: design — Gantree Structure Design

Top-Down BFS hierarchical decomposition → down to atomic nodes. Reference: **PG skill** (Gantree/PPR canonical) + this SKILL.md "PGF Notation Extensions" section for PGF-specific status codes.

**Completion criteria:** (1) All leaves = atomic nodes (2) PPR def written for complex nodes (3) No circular @dep (4) Checklist passed

### Step 2: plan — WORKPLAN Generation

DESIGN-{Name}.md → WORKPLAN-{Name}.md conversion. Reference: `workplan-reference.md §2`

### Step 3: execute — Sequential Node Execution

Node execution based on WORKPLAN-{Name}.md. For `[parallel]` nodes, use the current runtime's parallel subagent/worktree capability when available; otherwise execute sequentially while preserving dependency order. Reference: `workplan-reference.md §4`

### Step 4: verify — Cross-Verification

Details: `{SKILL_DIR}/reference/verify-reference.md`

3-perspective verification:
1. **Acceptance Criteria** — Re-check acceptance_criteria from DESIGN PPR (Lightweight: `# criteria:` inline)
2. **Code Quality** — runtime review/simplify capability or direct inspection, verifying reuse/quality/efficiency of changed code
3. **Architecture** — Compare DESIGN Gantree ↔ actual implementation structure (Lightweight: skip)

Result: `passed` → complete / `rework` → rollback target node + re-execute subtree / `blocked` → report to user.
Rework iterations are allowed up to `POLICY.max_verify_cycles`.

### full-cycle

Details: `{SKILL_DIR}/reference/cycle-reference.md` (covers both `full-cycle` and `create` modes)

Automatically execute design → plan → execute → verify as one continuous process. On rework during verify, roll back only the affected subtree and re-execute (up to `POLICY.max_verify_cycles` times). On session interruption, resume from the last Phase recorded in WORKPLAN/status JSON.

**Phase transition conditions:**

| Transition | Condition | On failure |
|------------|-----------|------------|
| discover → design | `auto_select_idea()` succeeds (**create mode only**) | 0 votes → abort |
| design → plan | All 4 completion criteria met | continue design |
| plan → execute | WORKPLAN + status JSON generated | report error |
| execute → verify | All nodes terminal | continue execute |
| verify → complete | passed | rework or report |

**Opt-in design review (`--with-review[=N]`)**

기본 풀사이클은 변경하지 않는다. 사용자가 명시적으로 `--with-review` 플래그를 줄 때만 design → plan 사이에 review 게이트를 삽입한다.

| Invocation | 동작 |
|---|---|
| `/PGF full-cycle X` | 기본 동작 (review 없음) |
| `/PGF full-cycle X --with-review` | review 1회 삽입 (N=1 기본) |
| `/PGF full-cycle X --with-review=3` | 최대 3회 review-revise 반복 |
| `/PGF create X --with-review=2` | create 모드도 동일 플래그 적용 |

**review 게이트 동작** (`reference/design-review-reference.md` 참조):
1. design 완료 직후 다관점 SubAgent 검토 실행 (PG/PGF 표기법, 보안, 프로토콜, 아키텍처)
2. 결과 분류: `Critical=0, High≤2` → plan 진행. 그 외 → DESIGN revise 후 재검토
3. revise 횟수 ≤ N. N회 초과 시 잔여 이슈 보고 + 사용자 승인 시 plan 진행 (강제 차단 아님)
4. status JSON에 `review_iterations`, `unresolved_issues` 만 추가 — 기존 키 불변

**Skip rules** (Level 1/Micro에 강제 적용 시 과잉이므로 자동 스킵):
- Level 1 (≤3 노드) → 플래그 무시, review 스킵
- `micro` 모드 → 플래그 무시
- Level 2 이상 → 플래그 적용

### Step 5: loop — Runtime-Adapter Auto-Execution

Details: `{SKILL_DIR}/loop/loop-reference.md`

| Command | Action |
|---------|--------|
| `/PGF loop start` | Initialize loop + execute first node |
| `/PGF loop cancel` | Cancel active loop |
| `/PGF loop status` | Report progress status |

On `/PGF loop start` or natural-language equivalent: (1) Verify WORKPLAN exists (2) initialize `.pgf/runtime/pgf-loop-state.json` (3) Determine mode (DESIGN exists → Standard / absent → Lightweight) (4) Select first node + load execution spec (5) Begin implementation. Afterwards, a runtime adapter continues the next node automatically when supported, or emits the next-node prompt for manual/agent continuation.

**Lightweight mode**: Loop execution with WORKPLAN only, without DESIGN. `#` inline comments under WORKPLAN nodes serve as PPR substitutes. Suitable for simple tasks, documentation, refactoring, etc.

### Step 6: discover — IdeaFirst Persona Multi-Agent Discovery

Details: `{SKILL_DIR}/discovery/discovery-reference.md`

| Command | Action |
|---------|--------|
| `/PGF discover` | Execute all 7 stages |
| `/PGF discover --from-step N` | Restart from stage N |
| `/PGF discover --personas N` | Use N personas |

Invoke 14 `{SKILL_DIR}/agents/pgf-persona-p*.md` personas in parallel when the runtime supports subagents. If not, simulate personas sequentially in the current runtime. Model hints inside persona files are advisory only. Integrate results from each stage → save to `.pgf/discovery/{step}.md`. HAO principle: do not enforce output format, preserve originals unedited.

### Step 7: create — Autonomous Creation Cycle

Details: `{SKILL_DIR}/reference/cycle-reference.md` (unified spec — `create` is the 5-phase autonomous variant)

| Command | Action |
|---------|--------|
| `/PGF create` | 5-Phase autonomous execution (DISCOVER→DESIGN→PLAN→EXECUTE→VERIFY) |
| `/PGF create --skip-discover` | Start from design using existing final_idea.md |

Fully autonomous execution without user approval. STEP 7 is replaced by `auto_select_idea` (vote-based automatic selection).

### Step 8: micro — Zero-Overhead Small Task Execution

Details: `{SKILL_DIR}/reference/micro-reference.md`

| Command | Action |
|---------|--------|
| `/PGF micro "task description"` | Inline decomposition → serial execution → minimal verify |

Entry: nodes ≤ 10, depth ≤ 3, no external deps, ≤ 30 min. Bypasses WORKPLAN/POLICY/status JSON. In-memory status only. Auto-promotes to full WORKPLAN if bounds exceeded.

### Step 9: delegate — AI-to-AI Task Handoff

Details: `{SKILL_DIR}/reference/delegate-reference.md`

Auto-triggered during execute when `should_delegate()` → True (capability gap, load balancing, parallel opportunity). Packages context into PG TaskSpec with AuthorityBounds → handshake → await result → validate → merge. Delegation chain tracks depth (max 3) and prevents cycles.

### Session Learning (횡단 — 모든 모드)

Details: `{SKILL_DIR}/reference/session-learning-reference.md`

- **Session start**: Load `.pgf/patterns/` → adapt POLICY defaults
- **Session end**: Record `SessionOutcome` to `.pgf/sessions/{id}.outcome.json`
- **Every 10 sessions**: Re-accumulate patterns (successful strategies, common blockers)

---

## Scale Detection and Strategy

> PG는 3-Level(Level 1~3)을 정의한다. PGF는 이를 상속하고 Large/Multi-agent를 추가한다.

| Scale | Criteria | Strategy |
|-------|----------|----------|
| **Level 1** | nodes ≤ 3 | 자연어 인라인 실행 — PG 파일 없음 |
| **Level 2** | nodes 4–10 | Gantree + `#` 주석 — 선택적 파일 |
| **Level 3** | nodes 11–30 | Full DESIGN + WORKPLAN + status JSON |
| **Large** | nodes > 30 or `(decomposed)` | Module separation + runtime-supported context compaction/checkpointing |
| **Multi-agent** | `[parallel]` with specialized tasks | `delegate` mode — AI-to-AI handoff |

> **Progressive Formalization**: Level 판단은 자동. 자연어 입력 → AI가 복잡도 평가 → 적합한 Level 선택. 실행 중 승격 시 기존 상태 보존.

## Execution Rules

1. Parse Gantree → determine hierarchy via indentation
2. Status codes → decide execute/skip
3. `@dep:` → determine execution order
4. `[parallel]` → concurrent processing
5. PPR `def` present → interpret and execute / `AI_` inline → execute directly / no PPR → recurse into children
6. Atomicity judgment → 15-minute rule
7. Failure → Failure Strategy + AI Redesign Authority
8. **Agent dispatch → PG TaskSpec** — 에이전트 파견 시 자연어 대신 `agent-protocol.md`의 PG TaskSpec 형식 사용. 입출력 타입, acceptance_criteria, failure_strategy를 구조화하여 전달
9. **Session start → load patterns** — `.pgf/patterns/`에서 과거 패턴 로드 → POLICY 자동 적응
10. **Session end → record outcome** — `.pgf/sessions/{id}.outcome.json`에 SessionOutcome 자동 기록

## Runtime Integration

| Capability | Runtime-neutral rule |
|-------|-------------|
| Parallel execution | Execute independent nodes within `[parallel]` blocks using available subagents, workers, worktrees, or sequential fallback |
| Code quality review | During verify, run the runtime's review/simplification tool if available; otherwise perform direct code review against acceptance criteria |
| Context compaction/checkpointing | For long runs, preserve WORKPLAN path, status JSON, and `.pgf/runtime/pgf-loop-state.json` before compaction or handoff |

---

## PGF Execution Checklist

> 기본 Gantree/PPR 작성 체크리스트는 **PG 스킬** 참조. 아래는 PGF 실행 단계 고유 항목.

### Execution Phase

- [ ] WORKPLAN-{Name}.md의 모든 노드 status가 terminal(`done`/`blocked`)인가
- [ ] status-{Name}.json의 summary가 WORKPLAN과 일치하는가
- [ ] `(blocked)` 노드에 blocker 사유가 기록되었는가

### Verify Phase (3-Perspective)

- [ ] **Acceptance**: 완료된 각 노드의 `acceptance_criteria` 재검증 (Lightweight: `# criteria:` 인라인)
- [ ] **Code Quality**: 변경된 코드를 런타임의 review/simplify 도구 또는 직접 검토로 재사용/품질/효율성 검증
- [ ] **Architecture**: DESIGN Gantree ↔ 실제 구현 구조 비교 (Lightweight: skip)
- [ ] Verdict 기록: `passed` / `rework` / `blocked`
- [ ] Rework 시: 대상 노드 + 자식 롤백 → 재실행 → 재검증 (`max_verify_cycles` 이내)
- [ ] Blocked 시: 사유 문서화 + 사용자 보고

### full-cycle Mode

- [ ] design → plan 전이 전 4가지 완료 기준 충족
- [ ] plan → execute 전이 시 WORKPLAN + status JSON 존재 확인
- [ ] execute → verify 전이 시 모든 노드 terminal 확인
- [ ] Verify rework 시 대상 서브트리만 롤백 (전체 reset 금지)
- [ ] `max_verify_cycles` 초과 시 산출물 보존 + abort 보고
- [ ] 세션 중단 시 WORKPLAN/status JSON에서 재개 가능 확인

### Discovery Archive

- [ ] 실행 완료 후 `archive-discovery` 스크립트 실행
- [ ] 아카이브 디렉토리가 날짜(YYYY-MM-DD) 단위로 분리되었는가
- [ ] `create` 모드: Phase 1 완료 직후 자동 아카이브

### Delegation & Micro Extensions

- [ ] `AI_make_` 사역 패턴이 필요한 곳에 사용되었는가
- [ ] ≤10 노드 작업에 `micro` 모드 사용을 검토했는가
- [ ] 병렬 에이전트 파견 시 PG TaskSpec 형식을 사용했는가
- [ ] `delegate` 시 AuthorityBounds(can_create/can_modify/forbidden)를 명시했는가
- [ ] Delegation chain depth ≤ 3 확인했는가
- [ ] 세션 완료 시 SessionOutcome을 기록했는가
- [ ] `(delegated)`/`(awaiting-return)`/`(returned)` status를 적절히 사용했는가
