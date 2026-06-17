# work-as-program — 작업 자체를 pg로 프로그래밍하는 법 (실행 가이드)

> PG의 본질: **"작업 그 자체"를 1급 프로그램으로 만든다. AI가 런타임이다.** 라이브러리(pgf)에 없는
> 형식의 작업은 pg로 *작업을 프로그래밍*한다 — 설계·시뮬레이션·실행·재설계. SKILL.md가 표기를 *정의*하면,
> 이 문서는 그 표기로 **작업 과정 자체를 다루는 절차**를 준다.

---

## 0. 동형성 (왜 "프로그래밍"인가)

```
일반 프로그래밍:  소스코드 → 컴파일러 → 기계가 실행
pg:              Gantree(구조) + PPR(로직) → AI 런타임이 실행
                 ├ PPR 시뮬레이션으로 실행 *전* 검증 (돌려보지 않고 통과/실패 예측)
                 ├ acceptance_criteria로 실행 *후* 검증
                 └ AI_redesign으로 작업 자체를 디버깅
```
→ 작업 과정이 설계·시뮬·테스트·검증·재설계 가능한 프로그램이 된다. pgf는 그 위의 stdlib.

## 1. 7단계 루프 (큰/새 작업의 표준)

라이브러리 모드(design/full-cycle 등)로 안 떨어지는 작업은 이 루프로 *프로그래밍*한다:

```text
① 분석    pgf design --analyze 로 대상을 역공학 → pg(Gantree)로 구조 저장
② 설계    통합/목표 구조를 pg로 설계·저장
③ 작업설계 구체화 작업설계서(WORKPLAN)를 pg로 설계 → .pgf/ 에 영속 (resume 가능)
④ 시뮬레이션 ★ PPR로 작업설계서를 심볼릭 실행 → 실행 *전* 위험 예측 (§2)
⑤ 실행    작업설계서대로 배치 실행 + 배치별 검증 게이트
⑥ 재설계  오류 시 pg로 재설계 (Failure Strategy / AI_redesign — 공개 인터페이스 보존)
⑦ 체크포인트 status JSON 갱신 → 중단/컨텍스트 단절에도 무손실 재개
```

원칙: **상태는 파일(`.pgf/`)에 둔다**(메모리·문서 하드코딩 금지). 한 단계의 실패가 누적 상태를 오염시키지 않게 격리.

## 2. ★ PPR 시뮬레이션 — 실행 전 사전검증 (가장 저평가된 능력)

작업설계서를 *돌리기 전에* PPR로 각 노드를 심볼릭 실행해 결과를 예측하고 위험을 미리 잡는다.

```python
def AI_simulate_workplan(plan: Gantree, env: dict) -> SimVerdict:
    """각 배치를 심볼릭 실행 → 산출/위험/acceptance 예측. 실제 파일변경 없음."""
    risks, checks = [], []
    for node in plan.topological_order():
        out = AI_predict_outcome(node, env)            # 이 노드가 무엇을 낳는가
        risks += AI_find_risks(node, env)              # 누락·충돌·순서 위험
        checks.append(Check(node.id, predict=out.acceptance_pass))
    verdict = "GO" if not any(r.severity == "high" for r in risks) else "REDESIGN"
    return SimVerdict(verdict, risks, checks)
    # acceptance_criteria:
    #   - high severity 위험 0 → GO
    #   - 실행 후 실측이 예측 check와 일치하면 시뮬레이션 신뢰 확정
```

**예측표 양식** (시뮬레이션 산출 → 실행 후 대조):

| 예측(노드) | 값 | 실행 후 실측 | 일치 |
|---|---|---|---|
| ... | ... | ... | ✅/❌ |

**실증**: HELIX 모노레포 마이그레이션에서 시뮬레이션이 *"`.py` 경로의 Path 파트(`".agents" / "skills"`)는 문자열 치환만으론 누락된다"*는 위험을 **실행 전에** 포착 → 치환 스크립트에 정규식을 선반영해 누락 0으로 통과. (`D:/HELIX/specs/META-PROGRAM.pg.md` §5.)

## 3. 재설계 (오류 시 디버깅)

```python
for batch in plan.topological_order():
    if batch.status == "done": continue              # idempotent — resume
    result = AI_execute(batch)
    if not AI_verify(result, batch.gate):
        batch.ppr = AI_redesign(batch, result.failure, constraint="preserve_gate")  # pg로 재설계
        result = AI_execute(batch)                   # 재실행
    record_status(".pgf/status.json", batch, result) # 영속 → 재개점
```
핵심: **공개 인터페이스(gate)는 보존**하고 내부 구현만 AI가 재설계한다.

## 4. 체크리스트

- [ ] 큰/새 작업을 Gantree로 분해해 `.pgf/`에 영속 저장했는가
- [ ] 실행 전 PPR 시뮬레이션으로 위험 예측표를 만들었는가 (high risk 0 → GO)
- [ ] 배치마다 검증 게이트를 두고, status JSON으로 재개 가능하게 했는가
- [ ] 오류를 `AI_redesign`(gate 보존)으로 디버깅했는가
- [ ] 상태를 파일에서 매번 재로딩하는가 (메모리/문서 하드코딩 금지)

> 관련: 제어흐름·도급 패턴 → [`control-flow-cookbook.md`](./control-flow-cookbook.md). 실행 규율(영속·증거검증·결정론) → pgf `reference/execution-discipline.md`.
