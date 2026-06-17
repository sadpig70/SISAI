# integration-doctrine — 통합/융합 판정 + 메타 폐루프 패턴 (실행 가이드)

> 두 산출물·시스템을 합칠 때 *고를지·통합할지·융합할지*를 정하는 게이트와, "닫혔으나 좁아지지 않는"
> 메타 폐루프(idea-layer) 패턴. 실증: recreate `select-or-integrate`, recreate⊕aox→HELIX(federate vs fuse).

---

## 1. Select vs Integrate (산출물 합치기)

두 후보가 있을 때 argmax로 하나 고르지(select) 말고, 상보면 제3으로 통합(integrate)한다.

```python
overlap        = AI_assess_overlap(a, b)            # 결과물 중복도 0~1
complementarity= AI_assess_complementarity(a, b)    # 같은 문제·다른 강점축?
if overlap >= 0.7:                          verdict = "duplicate"   # 하나 버림
elif overlap < 0.4 and complementarity >= 0.5: verdict = "integrate" # 제3으로 통합
else:                                       verdict = "independent" # 각자 select
```

**통합 채택 게이트 (능가할 때만)**: 통합은 input contract를 넓혀 buildability·boundary를 거의 항상 잃는다.
이를 상쇄하려면 **세 조건이 함께**:
1. 강한 same_problem,
2. **구조적으로 정렬된 상보축**(시간축 lifecycle·인과·파이프라인 단계),
3. 부모 단독으로 못 보는 **고유가치**(예: 단계 간 모순).
→ 셋이 있을 때만 통합이 부모 최고점을 능가. 아니면 폐기(원본 유지). margin 근소(±0.1)면 cross-model 합의로 검증.

## 2. Fuse vs Federate (시스템 합치기)

목표가 판정을 바꾼다.

| 목표 | 답 |
|---|---|
| 두 시스템을 *따로 유지보수* | **federate** — 공유 substrate(단일 출처) + 어댑터로 연결 |
| repo *하나로 모든 기능 수행*(자기완결 배포) | **vendor/fuse** — 전부 포함, 단 내부 로직은 단일 출처(*패키징은 융합, 로직은 단일출처*) |

> 함정: 큰 복사 작업의 번거로움을 "아키텍처 우월성(federate)"으로 포장하지 말 것. **사용자의 실제 목표**가
> "자기완결"이면 vendor가 정답이다. 단 vendor해도 중복 로직은 백본에 한 번만 정의해 desync를 막는다.
> 실증: recreate⊕aox → HELIX. 처음엔 federate 권고였으나 "repo 하나로 전 기능" 목표엔 vendor가 정답이었다.

## 3. 메타 폐루프 (idea-layer) — 닫혔으나 안 좁아지는 나선

반복 생성은 동질화(출력 수렴)로 좁아진다. 이를 **상류 의도 + 하류 게이트 + 환류**로 제어한다.

```text
IdeaKernel(상류 의도)  →  6 primitive의 *목표* 선언 (NoNameFirst)
   ↓
6 게이트(하류 측정)    →  diversity·tournament·evaluator·cross-model·provenance가 *달성* 측정
   ↓
kernel_gap(환류)       →  의도 대비 달성 gap → 다음 kernel 조향 (NoOpenLoop)
```
- 같은 6 primitive를 **두 지점**(의도 선언 / 달성 측정)에서 표현 → 단일 측정으로 desync 제거.
- "원이 아니라 나선": 백본(desync 제거) × 다양성 게이트(폭 유지) × 환류(전진) → 폐루프인데 수렴 안 함.

```python
def AI_measure_kernel_gap(kernel, measured) -> dict:
    gap = {p: kernel.target[p] - measured[p] for p in PRIMITIVES}
    gap["next_emphasis"] = AI_rank_by_gap(gap)        # gap 큰 primitive → 다음 라운드 강화
    return gap                                        # registry에 누적 → 환류
```

## 4. 동질화 차단 다지점화

단일 게이트로 부족하면 입력→중간→출력 여러 지점에서 막는다.
- 실증(IdeaFirst): 입력(sdxx)→인사이트(idxx)→카테고리(cixx) 3점 + recreate avoidance + cross-model = 5점.
- 측정은 **백본 단일 함수**(`measure_diversity`)로, 트리거는 각 지점에서 — 임계 복제 금지(desync 방지).

## 5. 체크리스트

- [ ] 합치기 전 overlap/complementarity 측정 → select/integrate/independent 판정
- [ ] 통합은 same_problem+정렬축+고유가치 3조건 충족 시만(능가 게이트). margin 근소면 cross-model
- [ ] fuse/federate는 **사용자 목표**로 판정(자기완결 → vendor + 단일출처 백본)
- [ ] 반복 생성엔 메타 폐루프(kernel→게이트→gap 환류) — NoOpenLoop
- [ ] 동질화는 단일 측정 + 다지점 트리거(임계 복제 금지)

> 실행 안전 규율 → [`execution-discipline.md`](./execution-discipline.md). 대규모 통합 절차 → [`large-work-playbook.md`](./large-work-playbook.md).
