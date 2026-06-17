# large-work-playbook — 대규모·다파일 작업 플레이북 (실행 가이드)

> 30노드↑ / 다파일 / 마이그레이션·통합 같은 큰 작업을 실수 없이 끝내는 절차. pgxf 인덱스 + 배치 +
> 안전 치환을 결합한다. 실증 템플릿: HELIX 모노레포 통합(`D:/HELIX`, 19스킬·207파일 vendoring).

---

## 1. 언제 이 플레이북인가

- 노드 > 30, 또는 `(decomposed)` 분리, 또는 여러 파일/스킬을 가로지르는 변경.
- 두 시스템 통합, 대량 vendoring, 경로 정규화, 스키마 일괄 변경 등.

## 2. pgxf 인덱스 (조감 + 노드 검색)

대규모 PG는 전체를 컨텍스트에 올리지 않는다. pgxf로 인덱스를 만들어 lazy-load·O(1) 노드 lookup·상태 집계.
- 진입 시 인덱스만 로드, 필요한 서브트리만 펼친다.
- `(decomposed)` 분리 트리는 인덱스가 참조로 연결.

## 3. 분해 → 영속 WORKPLAN (배치 = 도급 단위)

```text
B0 Skeleton    디렉토리/스캐폴드
B1..Bk         독립 배치 (각 @dep + 검증 게이트)
B(k+1) Normalize 가로지르는 일괄 변경 (경로/스키마) — 복사 완료 후 1회
B(last) Verify  전체 게이트
```
status JSON에 배치 상태 → 중단/재개 안전. **복사는 idempotent**(덮어쓰기 안전)하게 설계.

## 4. 인벤토리 먼저 (근거 있는 계획)

추정 금지. 규모를 실측해 계획을 정초한다.
```bash
find <src> -type f | wc -l          # 파일 수
diff -rq <treeA> <treeB>            # 중복/분기 식별 (dedup 결정)
grep -rl "<old-path>" <tree> | wc -l   # 정규화 범위
```
> HELIX 실증: IdeaFirst 121파일 + recreate 52파일 인벤토리 → pg/pgf/pgxf 중복 발견 → dedup 결정.

## 5. 안전 치환 (정규화 배치)

가로지르는 일괄 변경은 **원자적**으로: 모든 앵커가 정확히 1회 매칭될 때만 일괄 기록.

```python
# 모든 치환 검증 후에만 쓰기 (부분 실패가 파일을 깨지 않게)
results, errors = {}, []
for f, edits in PLAN.items():
    txt = read(f)
    for old, new in edits:
        if txt.count(old) != 1: errors.append((f, old)); continue   # 앵커 1회 매칭 강제
        txt = txt.replace(old, new, 1)
    results[f] = txt
if errors: abort(errors)            # 하나라도 실패 → 기록 안 함
for f, txt in results.items(): write(f, txt)
```

**보존 규칙** (마이그레이션이 깨기 쉬운 것 — 반드시 보존):
- **줄바꿈**: 파일별 원본 CRLF/LF 보존(`autocrlf` 환경에서 whole-file diff 방지). 정규화→편집→원본 줄바꿈으로 복원.
- **일반화/개선분**: 대상이 *독자 진화*했으면 소스로 덮어쓰지 말 것(퇴행). 가산만.
- **상호참조 무결성**: 경로 변경 후 `grep -rl "<old>"` = 0 확인, 링크 대상 존재 확인.

## 6. 검증 (배치마다 + 전체)

```text
- 배치 게이트: 파일 수 = 소스 합, 앵커 dangling = 0, py_compile OK
- 전체: unittest OK · validate PASS · 회귀 없음 (기존 테스트 수 유지)
- 인벤토리 매트릭스: 모든 항목(스킬/모듈)이 목적지에 매핑됨을 표로 증명 (빠짐없음)
```

## 7. 체크리스트

- [ ] 인벤토리 실측(파일수·중복·정규화 범위)으로 계획 정초
- [ ] WORKPLAN 배치 + status 영속 (idempotent 복사)
- [ ] 일괄 치환은 원자적(앵커 1회 매칭) + 줄바꿈/개선분/상호참조 보존
- [ ] 커버리지 매트릭스로 빠짐없음 증명
- [ ] 배치별·전체 게이트 통과 (회귀 0)

> 실행 안전 규율(영속·증거검증·결정론) → [`execution-discipline.md`](./execution-discipline.md).
> 통합 vs 융합 판정 → [`integration-doctrine.md`](./integration-doctrine.md).
