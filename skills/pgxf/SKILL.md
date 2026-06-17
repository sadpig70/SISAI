---
name: pgxf
description: "PGXF (PPR/Gantree IndeX Framework) — file-based index system for ultra-large PG structures. Enables lazy-load subtree access, O(1) node lookup, cross-file status aggregation, and automatic sync with (decomposed) splits. Triggers: 인덱스, 대규모 설계, 노드 찾기, 구조 조감, 상태 집계, pgxf, index, large-scale, node lookup, status aggregate, 전체 구조 파악, 어디에 있는지, 노드 검색. Use this skill whenever a PG/PGF project exceeds 30 nodes, spans multiple files, uses (decomposed) splits, or when the user needs to locate/navigate/aggregate across a large PG tree without loading everything into context."
user-invocable: true
argument-hint: "build|lookup|sync|status|prune [project-name|node-name]"
---

# PGXF — PPR/Gantree IndeX Framework v1.0

> PG가 언어, PGF가 라이브러리라면, **PGXF는 파일 시스템 인덱스**다.
> 컨텍스트 윈도우에 전체 트리를 로드하지 않고, 필요한 노드만 정밀 접근한다.

## 배경: 왜 PGXF가 필요한가

PG/PGF 프로젝트가 성장하면 다음 한계에 도달한다:

| 한계 | 증상 | PGXF 해결 |
|------|------|-----------|
| 컨텍스트 폭발 | 노드 50+ → 전체 트리 로드 불가 | **Lazy Load** — 인덱스만 로드, 서브트리는 요청 시 |
| 탐색 비용 | "이 노드 어디 파일에 있지?" → 전체 스캔 | **O(1) Lookup** — 노드명 → 파일:라인 즉시 반환 |
| 상태 파악 불가 | 분산된 status를 수동 집계 | **Aggregate** — 인덱스 레벨에서 전체 done/total 즉시 |
| `(decomposed)` 추적 유실 | 분리된 트리 참조 끊김 | **Cross-ref** — decomposed 링크 자동 추적 |

## PG 기반 의존성

**PGXF는 PG(PPR/Gantree) 표기법과 PGF(Framework)를 기반으로 한다.**

- PG 스킬: Gantree 노드 문법, PPR 구문, `(decomposed)` 규칙
- PGF 스킬: DESIGN/WORKPLAN/status 파일 포맷, 실행 모드

PGXF는 이들 위에 **인덱스 계층**을 추가한다. PG/PGF의 문법·규칙을 재정의하지 않는다.

---

## Quick Start

```bash
# 1. 프로젝트 인덱스 빌드
/pgxf build MyProject

# 2. 노드 찾기
/pgxf lookup PaymentProcessor

# 3. 전체 상태 조감
/pgxf status MyProject

# 4. 소스 변경 후 인덱스 동기화
/pgxf sync MyProject

# 5. 삭제된 노드 정리
/pgxf prune MyProject
```

---

## 핵심 개념

### Index Entry (노드 단위 인덱스)

PGXF의 최소 단위. **하나의 PG 노드 = 하나의 Index Entry**.

```python
IndexEntry = {
    "node":        str,              # CamelCase 노드명 (유일 식별자)
    "status":      str,              # done | in-progress | designing | blocked | decomposed | ...
    "file":        str,              # 소속 파일 경로 (상대)
    "line":        int,              # 파일 내 시작 줄 번호
    "depth":       int,              # 트리 깊이 (0 = root)
    "parent":      Optional[str],    # 부모 노드명
    "children":    list[str],        # 자식 노드명 목록
    "deps":        list[str],        # @dep: 의존성
    "has_ppr":     bool,             # PPR def 블록 존재 여부
    "ppr_file":    Optional[str],    # PPR 정의 파일 (별도 파일인 경우)
    "ppr_line":    Optional[int],    # PPR 시작 줄
    "decomposed_to": Optional[str],  # (decomposed) 시 분리된 트리 파일
    "tags":        list[str],        # #tag 목록
}
```

### Index File (프로젝트 인덱스)

```
.pgxf/
    INDEX-{Name}.json          # 프로젝트 인덱스 (노드 레지스트리)
    MANIFEST.json              # 멀티 프로젝트 매니페스트 (선택)
```

### Manifest (멀티 프로젝트)

하나의 워크스페이스에 여러 PGF 프로젝트가 공존할 때, MANIFEST가 전체를 조감한다.

```json
{
  "workspace": "SeAAI",
  "projects": [
    {
      "name": "AionEngine",
      "index": ".pgxf/INDEX-AionEngine.json",
      "design": ".pgf/DESIGN-AionEngine.md",
      "total_nodes": 47,
      "done": 31,
      "status_summary": {"done": 31, "in-progress": 8, "designing": 5, "blocked": 3}
    },
    {
      "name": "PGTPProtocol",
      "index": ".pgxf/INDEX-PGTPProtocol.json",
      "design": ".pgf/DESIGN-PGTPProtocol.md",
      "total_nodes": 23,
      "done": 23,
      "status_summary": {"done": 23}
    }
  ],
  "global_summary": {"total": 70, "done": 54, "in-progress": 8, "designing": 5, "blocked": 3},
  "updated_at": "2026-04-11T09:00:00"
}
```

---

## 실행 모드

| Mode | Trigger | Action |
|------|---------|--------|
| `build` | "인덱스 빌드", "index build" | PGF 소스 스캔 → INDEX-{Name}.json 생성 |
| `lookup` | "노드 찾기", "어디에 있는지" | 노드명 → 파일:줄, PPR 위치, 상태 반환 |
| `sync` | "동기화", "인덱스 갱신" | 소스 변경분 감지 → 인덱스 증분 업데이트 |
| `status` | "상태 조감", "전체 현황" | 인덱스 기반 상태 집계 + 트리 요약 출력 |
| `prune` | "정리", "삭제 노드 제거" | 소스에서 사라진 노드를 인덱스에서 제거 |

### $ARGUMENTS 파싱

- `$ARGUMENTS[0]`: mode keyword
- `$ARGUMENTS[1:]`: 프로젝트명 또는 노드명
- 예: `/pgxf build SeAAI`, `/pgxf lookup PaymentProcessor`, `/pgxf status`

---

## Build 프로세스

### 입력 소스

```python
def pgxf_build(project_name: str) -> Index:
    """PGF 소스 파일들을 스캔하여 인덱스를 생성한다."""

    # 1. 소스 수집: .pgf/ 디렉토리의 DESIGN, WORKPLAN 파일
    sources = scan_pgf_dir(".pgf/", project_name)
    # → ["DESIGN-MyProject.md", "WORKPLAN-MyProject.md", ...]

    # 2. Gantree 파싱: 각 파일의 ## Gantree 섹션에서 노드 추출
    gantree_nodes = []
    for src in sources:
        nodes = extract_gantree_nodes(src)
        # 각 노드: name, status, depth, parent, children, deps, tags, line_number
        gantree_nodes.extend(nodes)

    # 3. PPR 매핑: ## PPR 섹션의 def 블록을 노드에 연결
    for node in gantree_nodes:
        ppr = find_ppr_def(sources, node.name)
        if ppr:
            node.has_ppr = True
            node.ppr_file = ppr.file
            node.ppr_line = ppr.line

    # 4. (decomposed) 추적: 분리된 트리 파일 참조 연결
    for node in gantree_nodes:
        if node.status == "decomposed":
            node.decomposed_to = resolve_decomposed_target(node, sources)

    # 5. 인덱스 생성 + 저장
    index = build_index(project_name, gantree_nodes)
    save_json(f".pgxf/INDEX-{project_name}.json", index)
    return index
```

### Gantree 노드 추출 규칙

들여쓰기 기반 파싱 — PG의 4-space 규칙 적용:

```
RootNode // desc (status) @v:1.0          → depth=0, parent=None
    ChildA // desc (done)                 → depth=1, parent=RootNode
        GrandchildA1 // desc (done)       → depth=2, parent=ChildA
    ChildB // desc (designing) @dep:ChildA → depth=1, parent=RootNode, deps=[ChildA]
```

**노드명 유일성 규칙**: 동일 프로젝트 내 노드명 중복 금지. 중복 발견 시 build에서 경고 + 파일:줄 표시.

### PPR def 블록 매칭

```python
# 노드명 → PPR 함수명 매칭 규칙
# CamelCase → snake_case 변환
# PaymentProcessor → payment_processor
# AI_ExtractKeywords → ai_extract_keywords (인라인은 매칭 불요)

def match_node_to_ppr(node_name: str, def_name: str) -> bool:
    return camel_to_snake(node_name) == def_name
```

---

## Lookup 프로세스

```python
def pgxf_lookup(node_name: str, project: Optional[str] = None) -> LookupResult:
    """노드명으로 위치·상태·PPR·의존성을 즉시 반환한다."""

    # 프로젝트 미지정 시 → MANIFEST에서 전체 검색
    if not project:
        project = find_project_containing(node_name)

    index = load_index(project)
    entry = index.nodes[node_name]

    return LookupResult(
        node=entry.node,
        status=entry.status,
        location=f"{entry.file}:{entry.line}",
        ppr_location=f"{entry.ppr_file}:{entry.ppr_line}" if entry.has_ppr else None,
        parent=entry.parent,
        children=entry.children,
        deps=entry.deps,
        decomposed_to=entry.decomposed_to,
    )
```

### Lookup 출력 예시

```
[PGXF] PaymentProcessor
  📍 .pgf/DESIGN-OrderSystem.md:45
  📊 status: in-progress
  🔗 PPR: .pgf/DESIGN-OrderSystem.md:112  (def payment_processor)
  ⬆ parent: OrderSystem
  ⬇ children: ValidateCard, ChargeCard, SendReceipt
  ➡ deps: UserAuth, Database
  📦 decomposed: —
```

---

## Sync 프로세스

```python
def pgxf_sync(project_name: str) -> SyncResult:
    """소스 변경분을 감지하여 인덱스를 증분 업데이트한다."""

    old_index = load_index(project_name)
    new_index = pgxf_build(project_name)  # 전체 리빌드

    diff = compute_diff(old_index, new_index)
    # diff.added:    새로 추가된 노드
    # diff.removed:  삭제된 노드
    # diff.modified: 상태/위치/PPR 변경된 노드

    save_json(f".pgxf/INDEX-{project_name}.json", new_index)

    return SyncResult(
        added=len(diff.added),
        removed=len(diff.removed),
        modified=len(diff.modified),
        details=diff,
    )
```

### Sync 출력 예시

```
[PGXF] sync OrderSystem
  ✚ added: RefundFlow, RefundValidator (2)
  ✎ modified: ChargeCard (designing → in-progress), SendReceipt (designing → done) (2)
  ✖ removed: LegacyGateway (1)
  📊 total: 15 nodes | done: 9 | in-progress: 3 | designing: 2 | blocked: 1
```

---

## Status 프로세스

```python
def pgxf_status(project: Optional[str] = None) -> StatusReport:
    """인덱스 기반 상태 집계. 프로젝트 미지정 시 MANIFEST 전체."""

    if project:
        index = load_index(project)
        return aggregate_single(index)
    else:
        manifest = load_manifest()
        return aggregate_all(manifest)
```

### Status 출력 예시 (단일 프로젝트)

```
[PGXF] OrderSystem status
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  done         ████████████░░░░  9/15 (60%)
  in-progress  ████░░░░░░░░░░░░  3/15 (20%)
  designing    ██░░░░░░░░░░░░░░  2/15 (13%)
  blocked      █░░░░░░░░░░░░░░░  1/15 (7%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🔴 blocked: PaymentGateway (blocker: external API)
  🟡 decomposed: ShippingFlow → .pgf/DESIGN-ShippingFlow.md
  📁 files: 3 (DESIGN-OrderSystem.md, DESIGN-ShippingFlow.md, WORKPLAN-OrderSystem.md)
```

### Status 출력 예시 (멀티 프로젝트 — MANIFEST)

```
[PGXF] workspace status
  ┌─────────────────┬───────┬──────┬────────┬──────────┬─────────┐
  │ Project         │ Total │ Done │ In-Prg │ Designing│ Blocked │
  ├─────────────────┼───────┼──────┼────────┼──────────┼─────────┤
  │ AionEngine      │    47 │   31 │      8 │        5 │       3 │
  │ PGTPProtocol    │    23 │   23 │      0 │        0 │       0 │
  │ SeAAIHub        │    18 │   12 │      4 │        2 │       0 │
  ├─────────────────┼───────┼──────┼────────┼──────────┼─────────┤
  │ TOTAL           │    88 │   66 │     12 │        7 │       3 │
  └─────────────────┴───────┴──────┴────────┴──────────┴─────────┘
  global: 75% complete
```

---

## Prune 프로세스

```python
def pgxf_prune(project_name: str) -> PruneResult:
    """소스에서 사라진 노드를 인덱스에서 제거한다."""

    index = load_index(project_name)
    current_nodes = scan_current_nodes(project_name)
    orphans = [n for n in index.nodes if n not in current_nodes]

    for orphan in orphans:
        del index.nodes[orphan]

    save_json(f".pgxf/INDEX-{project_name}.json", index)
    return PruneResult(removed=orphans)
```

---

## (decomposed) 자동 추적

PGXF의 핵심 가치: `(decomposed)` 노드를 인덱스가 자동으로 크로스 레퍼런스한다.

### 시나리오

```
# DESIGN-OrderSystem.md
OrderSystem // 주문 시스템 (in-progress)
    PaymentFlow // 결제 흐름 — see DESIGN-PaymentFlow.md (decomposed)
    ShippingFlow // 배송 흐름 (designing)

# DESIGN-PaymentFlow.md (분리된 트리)
PaymentFlow // 결제 흐름 상세 (in-progress)
    ValidateCard // 카드 검증 (done)
    ChargeCard // 카드 청구 (in-progress) @dep:ValidateCard
    SendReceipt // 영수증 발송 (designing) @dep:ChargeCard
```

### PGXF build 결과

```json
{
  "project": "OrderSystem",
  "files": [
    ".pgf/DESIGN-OrderSystem.md",
    ".pgf/DESIGN-PaymentFlow.md"
  ],
  "nodes": {
    "OrderSystem": {
      "node": "OrderSystem", "status": "in-progress",
      "file": ".pgf/DESIGN-OrderSystem.md", "line": 3,
      "depth": 0, "parent": null,
      "children": ["PaymentFlow", "ShippingFlow"],
      "deps": [], "has_ppr": false,
      "decomposed_to": null, "tags": []
    },
    "PaymentFlow": {
      "node": "PaymentFlow", "status": "decomposed",
      "file": ".pgf/DESIGN-OrderSystem.md", "line": 4,
      "depth": 1, "parent": "OrderSystem",
      "children": ["ValidateCard", "ChargeCard", "SendReceipt"],
      "deps": [], "has_ppr": false,
      "decomposed_to": ".pgf/DESIGN-PaymentFlow.md",
      "tags": []
    },
    "ValidateCard": {
      "node": "ValidateCard", "status": "done",
      "file": ".pgf/DESIGN-PaymentFlow.md", "line": 4,
      "depth": 2, "parent": "PaymentFlow",
      "children": [], "deps": [], "has_ppr": false,
      "decomposed_to": null, "tags": []
    }
  },
  "summary": {"total": 6, "done": 1, "in-progress": 2, "designing": 1, "decomposed": 1, "blocked": 0},
  "updated_at": "2026-04-11T09:00:00"
}
```

**핵심**: `PaymentFlow`의 `children`에 분리된 파일의 자식들이 포함된다. 인덱스가 파일 경계를 넘어 트리를 재구성한다.

---

## Lazy Load 패턴

AI가 대규모 프로젝트 작업 시 PGXF를 활용하는 표준 패턴:

```python
def work_with_large_project(task: str, project: str):
    """대규모 프로젝트에서 특정 작업 수행 — 전체 로드 없이."""

    # 1단계: 인덱스만 로드 (경량)
    index = pgxf_load_index(project)

    # 2단계: 작업 대상 노드 식별
    target_nodes = AI_identify_relevant_nodes(task, index.summary)

    # 3단계: 해당 노드의 소스만 로드
    for node_name in target_nodes:
        entry = index.nodes[node_name]
        source = load_file_range(entry.file, entry.line, estimate_end(entry))
        if entry.has_ppr:
            ppr = load_file_range(entry.ppr_file, entry.ppr_line, estimate_ppr_end(entry))

    # 4단계: 작업 수행 후 인덱스 동기화
    execute_task(task, loaded_sources)
    pgxf_sync(project)
```

---

## 파일 경로 규칙

```text
<project-root>/
    .pgf/                              # PGF 소스 (기존)
        DESIGN-{Name}.md
        WORKPLAN-{Name}.md
        status-{Name}.json
    .pgxf/                             # PGXF 인덱스 (신규)
        INDEX-{Name}.json              # 프로젝트별 인덱스
        MANIFEST.json                  # 워크스페이스 매니페스트 (선택)
```

- `.pgxf/`는 `.pgf/`와 **동일 레벨**에 위치
- INDEX 파일은 소스가 아닌 **파생 산출물** — 언제든 rebuild 가능
- MANIFEST는 여러 INDEX를 집계하는 **메타 인덱스**

---

## PGF 연동

| PGF 이벤트 | PGXF 동작 |
|------------|-----------|
| `pgf design` 완료 | `pgxf build` 자동 트리거 |
| `pgf execute` 노드 상태 변경 | `pgxf sync` 권장 (수동) |
| `pgf loop` 시작 | index 로드하여 전체 구조 파악 후 실행 |
| `pgf full-cycle` 완료 | `pgxf sync` + `pgxf status` |
| `(decomposed)` 분리 발생 | 다음 `pgxf sync`에서 자동 추적 |

---

## 실행 규칙

1. `/pgxf build` — `.pgf/` 내 DESIGN/WORKPLAN 파일 전수 스캔 → INDEX 생성
2. `/pgxf lookup NodeName` — INDEX에서 O(1) 검색, 없으면 MANIFEST 검색
3. `/pgxf sync` — 전체 rebuild 후 diff 리포트
4. `/pgxf status` — INDEX/MANIFEST 기반 집계 출력
5. `/pgxf prune` — 소스에 없는 고아 노드 제거
6. 프로젝트명 생략 시 → 현재 디렉토리의 `.pgf/`에서 자동 감지
7. `.pgxf/` 디렉토리 미존재 시 → 자동 생성

---

## INDEX-{Name}.json 전체 스키마

상세 스키마와 필드별 규칙: `{SKILL_DIR}/references/pgxf-format.md`

> **Path convention**: `{SKILL_DIR}`는 이 스킬의 루트 디렉터리(SKILL.md가 있는 곳)를 가리키는 런타임 중립 placeholder다. 각 런타임이 로컬 설치 경로로 치환한다. 절대경로·런타임 종속 env var를 하드코딩하지 않는다 (PGF SKILL과 동일 규칙).

---

## 체크리스트

### Build 검증

- [ ] 모든 DESIGN/WORKPLAN 파일이 스캔되었는가?
- [ ] 노드명 중복이 없는가?
- [ ] `(decomposed)` 노드의 분리 파일이 존재하는가?
- [ ] PPR def 블록이 올바른 노드에 매핑되었는가?
- [ ] parent-children 관계가 양방향 일관성인가?

### Sync 검증

- [ ] added/removed/modified 카운트가 실제 변경과 일치하는가?
- [ ] summary 집계가 nodes 상태와 일치하는가?
- [ ] `decomposed_to` 참조가 유효한 파일을 가리키는가?

### 운영 규칙

- [ ] INDEX 파일은 파생물 — git에 포함 여부는 프로젝트 정책 (권장: .gitignore)
- [ ] MANIFEST는 선택 — 단일 프로젝트에서는 불필요
- [ ] 노드 50+ 프로젝트에서는 lookup 전 반드시 sync 확인
