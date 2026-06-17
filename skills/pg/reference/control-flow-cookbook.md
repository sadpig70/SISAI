# control-flow-cookbook — 타입 I/O · 조건 · 분기 · 반복 · 도급 (실행 가이드)

> pg는 작업의 **입출력을 타입으로 정의**하고 **조건·분기·반복**으로 흐름을 제어한다. 그래서 여러 도급
> 단위(스킬/에이전트)가 타입 계약으로 자재를 주고받는 **공장 생산라인 같은 복잡 작업**도 프로그래밍할 수 있다.
> SKILL.md가 문법을 *정의*하면, 이 문서는 그 문법을 **복잡 작업 오케스트레이션에 쓰는 패턴**을 모은다.

---

## 1. 타입 I/O — 라인을 흐르는 "자재"

도급 단위가 주고받는 자재를 타입으로 정의한다(계약의 핵심). Python 타입힌트 + 스키마 리터럴(PG 허용).

```python
ChannelCatalog = dict = {"version": str, "channels": list[Channel], "total": int}
TrendReport    = dict = {"industry_trend_md": str, "domains_covered": int}
Idea           = dict = {"id": str, "title": str, "domains": list[str], "scores": Scores6}
DesignSeed     = dict = {"name": str, "single_question": str, "sources": list[str]}
```

## 2. 도급 단위(contractor) — 입력계약 → 출력계약 + 검수

각 단위 = 하청. 입력 타입을 받아 출력 타입을 납품하고, acceptance를 통과해야 다음 공정.

```python
Contractor = dict = {"name": str, "input_type": type, "output_type": type,
                     "acceptance": list[str], "failure_strategy": Literal["retry","redesign","handoff"],
                     "max_retry": int}
```

## 3. 조건 · 분기 (Python 흐름 제어 그대로)

```python
# 환경 능력으로 라인 교체 (분기)
if env["cross_model"] == "available":   line = full_line
elif env["cross_model"] == "unavailable": line = swap(line, {"cix":"sa-icx","evx":"sa-evx"})
else:                                    line = mark_partial(line)

# 게이트 분기 (재사용 차단)
if is_consumed(candidate, ledger)["consumed"]:
    return "reject:re-steer"            # 폐기 → 재조향
```

## 4. 반복 (4종 패턴)

```python
# ① 공정 재시도 (max_retry)
for attempt in range(c["max_retry"] + 1):
    out = AI_invoke(c["name"], material)
    if AI_verify(out, c["acceptance"]): return out
    if attempt >= 1 and c["failure_strategy"] == "redesign":
        c["ppr"] = AI_redesign(c, out.failure)

# ② Convergence Loop (생성-비판-진화: 안정화까지)
while True:
    eval = AI_evaluate(draft, criteria)
    if eval.score >= threshold: break
    draft = AI_revise(draft, eval.feedback)

# ③ island 재발산 (다양성 미달 동안)
while unique_ratio(pool, sim) < floor:
    pool = regenerate(pool, focus=AI_find_untouched_axes(pool))

# ④ 생산 라운드 (목표/예산까지)
while len(out) < target and budget.remaining() > 0:
    out.append(run_one_round())
```

## 5. 메인 프로그램 — 타입 × 분기 × 반복 결합 (공장 라인)

```python
def run_factory(target: int, budget: int, env: dict) -> list[DesignSeed]:
    seeds = []
    while len(seeds) < target and budget_left(budget) > 0:        # 반복 ④
        line = AI_route_by_capability(env, LINE)                  # 분기 ①
        material = None
        for c in line:                                           # 도급 직렬
            material = run_stage(c, material)                    # 반복 ①(검수+재시도)
            if c["name"] == "cix":
                material = enforce_diversity(converge(material))  # 반복 ②③
        winner = material["winner"]
        if AI_gate(winner, ledger) == "reject:re-steer":         # 분기(게이트)
            continue                                              # 재조향 후 다음 라운드
        seeds.append(AI_to_seed(winner))
    return seeds
    # acceptance_criteria:
    #   - 각 도급 출력이 output_type·acceptance 충족 (공정 검수)
    #   - 반복은 종료성 보장 (target/budget 중 먼저 닿는 쪽)
```

## 6. [parallel] — 독립 공정 병렬

```python
[parallel]
recombine = AI_recombine(inv)      # 독립
mutate    = AI_mutate(inv)
transplant= AI_transplant(inv)
[/parallel]
pool = recombine + mutate + transplant     # 병합
```
규칙: `[parallel]` 내부 노드는 **독립**(`@dep:` 금지), 중첩 금지.

## 7. 실행 전 시뮬레이션 (도급 라인도 dry-run)

```python
def AI_simulate_factory(target, env) -> SimVerdict:
    line = AI_route_by_capability(env, LINE)   # 단독환경이면 sa-*로 교체될 것 예측
    # 반복④ 종료성·분기·병목을 라인 안 돌리고 미리 확인 → GO | REDESIGN
```

**실증**: `D:/HELIX/specs/PRODUCTION-LINE.pg.md` (HELIX 연속생산을 공장 도급 pg 프로그램으로),
`DESIGN-HELIX-UNIFIED-PIPELINE.pg.md` (aox·recreate 전 기능 단일 폐루프).

> 관련: 작업 자체를 프로그래밍하는 7단계 → [`work-as-program.md`](./work-as-program.md).
> 에이전트 간 도급 핸드오프 규격(TaskSpec) → pgf `reference/agent-protocol.md`.
