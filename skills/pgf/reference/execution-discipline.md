# execution-discipline — 실수 없이 끝내는 실행 규율 (실행 가이드)

> PGF로 큰 작업을 *실수 없이* 완수하는 규율. 모드(design/plan/execute/verify)가 *무엇을* 하는지는 다른
> reference가 정의하고, 이 문서는 **어떻게 안전하게 실행하는가**(분해·영속·증거검증·결정론 경계)를 준다.
> 실증 템플릿: HELIX(`D:/HELIX/.pgf/`)·recreate.

---

## 1. 분해 → 영속 → 배치 게이트 → 재개 (핵심 사이클)

큰 작업은 한 번에 하지 않는다. 분해해 저장하고 배치로 실행한다.

```text
1) 분해      Gantree로 배치(B0..Bn) 분해, 각 배치에 독립 검증 게이트
2) 영속      .pgf/{DESIGN,WORKPLAN,status}-{Name}.* 에 저장 (계획을 파일에)
3) 실행      배치 순서대로, 배치마다 게이트 통과 후 다음
4) 체크포인트 status JSON에 배치 상태 기록 ("done"/"blocked")
5) 재개      중단 시 status 읽어 첫 non-done 배치부터 (copies idempotent)
```

`status-{Name}.json` 최소 형태:
```jsonc
{"phase":"execute","summary":{"done":5,"total":8},
 "batches":{"B0":"done","B1":"done","B5":"pending"},
 "resume_rule":"read batches; start at first non-done; copies idempotent"}
```
> 효과: 한 턴에 못 끝내도 다음 턴이 status를 보고 정확히 이어받는다. 컨텍스트 단절에 무손실.

## 2. 증거 기반 검증 (★ 자기보고 신뢰 금지)

`status`에 `passed`라 적기 전에 **실제 명령을 실행하고 그 출력**을 증거로 남긴다.

```text
- python -m unittest discover -s tests   → OK (FAILED면 통과 금지)
- python -m py_compile <mods>            → 문법/경로 무결
- <app> sample / run examples/*.json     → 기대 출력 확인
- 동일입력 2회 실행 → 출력 일치 (결정론 확인)
```

**GATE-EVIDENCE** — 게이트 실측을 구조화 기록(전부 `passed:true`가 아니면 진행/공개 금지):
```jsonc
{"command":"python -m unittest discover -s tests","cwd":".","exit_code":0,
 "stdout_excerpt":"Ran 83 tests ... OK","passed":true,"artifact_checked":"tests/"}
```
> 교훈: "passed"를 추정·자기보고로 적지 말 것 — exit_code 근거로만 판정.

## 3. 3관점 verify (verify mode)

- **Acceptance**: DESIGN의 acceptance_criteria 재검증.
- **Quality**: 변경 코드의 재사용/중복/효율 (`/simplify` 류).
- **Architecture**: DESIGN Gantree ↔ 실제 구조 일치.
- Verdict: `passed` / `rework`(대상 서브트리만 롤백·재실행) / `blocked`(보고). `max_verify_cycles` 이내.

## 4. 결정론 경계 (설계 제약으로 강제)

```text
결정론 코어     → stdlib only, 시계/네트워크/AI 없음. 시간은 now 주입, 유사도는 sim 주입
메타층(AI_)     → 판단/창조 단계는 비결정론 허용 (엔진/설계 자산)
생성물 verdict  → 결정론 불변 (동일 입력 → 동일 출력)
wall-clock      → CLI 엣지에서만 (--now 주입 우선)
```
검사: `grep -rnE "datetime\.now|time\.time|random\.|utcnow" core/` 가 0이어야(코어 한정).
> 실증: HELIX-Core는 순수 stdlib, 시계는 `helix.py` CLI 엣지에만.

## 5. 안전 규칙 (되돌리기 어려운 작업)

- **원본 불변**: 정본·과거 산출·기존 엔트리는 수정 금지. 새 run/새 엔트리만 추가(자기 엔트리 status 전이만 허용).
- **idempotency 선검사**: 외부 생성(repo/파일) 전 존재 확인 → 있으면 재생성 금지(reconcile만). 삭제·force 금지.
- **누출 0**: 코드/문서/커밋에 타 런타임 식별자·미공개 내부명·PII 0.
- **fail-safe**: 손상 산출은 커밋 말고 격리/폐기. 의심 시 정지 후 보고.

## 6. 체크리스트

- [ ] `.pgf/{DESIGN,WORKPLAN,status}` 영속 + 배치별 게이트
- [ ] 모든 "passed"가 실측 GATE-EVIDENCE(exit_code) 근거인가
- [ ] 3관점 verify verdict 기록 (rework는 대상 서브트리만)
- [ ] 코어 결정론(시계/난수/외부의존 0) 확인
- [ ] 원본 불변 · idempotency 선검사 · 누출 0

> 대규모(>30노드)·다파일 마이그레이션 → [`large-work-playbook.md`](./large-work-playbook.md).
> 통합/융합 판정·메타 폐루프 → [`integration-doctrine.md`](./integration-doctrine.md).
