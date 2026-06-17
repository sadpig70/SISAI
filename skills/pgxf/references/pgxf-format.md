# PGXF Index Format Specification

> INDEX-{Name}.json과 MANIFEST.json의 상세 스키마 및 필드별 규칙.

---

## 1. INDEX-{Name}.json 전체 스키마

```json
{
  "pgxf_version": "1.0",
  "project": "ProjectName",
  "files": [
    ".pgf/DESIGN-ProjectName.md",
    ".pgf/DESIGN-SubModule.md",
    ".pgf/WORKPLAN-ProjectName.md"
  ],
  "nodes": {
    "NodeName": {
      "node":           "NodeName",
      "status":         "in-progress",
      "file":           ".pgf/DESIGN-ProjectName.md",
      "line":           12,
      "depth":          1,
      "parent":         "RootNode",
      "children":       ["ChildA", "ChildB"],
      "deps":           ["OtherNode"],
      "has_ppr":        true,
      "ppr_file":       ".pgf/DESIGN-ProjectName.md",
      "ppr_line":       87,
      "decomposed_to":  null,
      "tags":           ["#core"]
    }
  },
  "summary": {
    "total":        24,
    "done":         12,
    "in-progress":  5,
    "designing":    4,
    "blocked":      2,
    "decomposed":   1,
    "needs-verify": 0,
    "delegated":    0,
    "awaiting-return": 0,
    "returned":     0
  },
  "decomposed_links": [
    {
      "source_node": "PaymentFlow",
      "source_file": ".pgf/DESIGN-OrderSystem.md",
      "target_file": ".pgf/DESIGN-PaymentFlow.md",
      "target_root": "PaymentFlow"
    }
  ],
  "built_at":   "2026-04-11T09:00:00",
  "updated_at": "2026-04-11T10:30:00"
}
```

---

## 2. 필드별 규칙

### 프로젝트 레벨

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pgxf_version` | str | ✅ | PGXF 스키마 버전 ("1.0") |
| `project` | str | ✅ | CamelCase 프로젝트명 |
| `files` | list[str] | ✅ | 스캔된 소스 파일 목록 (상대 경로) |
| `nodes` | dict[str, IndexEntry] | ✅ | 노드명 → IndexEntry 매핑 |
| `summary` | dict[str, int] | ✅ | 상태별 집계 |
| `decomposed_links` | list[DecomposedLink] | ✅ | (decomposed) 크로스 참조 목록 |
| `built_at` | str (ISO8601) | ✅ | 최초 빌드 시각 |
| `updated_at` | str (ISO8601) | ✅ | 마지막 갱신 시각 |

### IndexEntry 필드

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node` | str | ✅ | CamelCase 노드 식별자 (프로젝트 내 유일) |
| `status` | str | ✅ | PG/PGF 상태 코드 |
| `file` | str | ✅ | 소속 파일 상대 경로 |
| `line` | int | ✅ | 파일 내 시작 줄 (1-based) |
| `depth` | int | ✅ | 트리 깊이 (root = 0) |
| `parent` | str \| null | ✅ | 부모 노드명 (root는 null) |
| `children` | list[str] | ✅ | 직계 자식 노드명 (빈 list 허용) |
| `deps` | list[str] | ✅ | @dep: 의존성 목록 (빈 list 허용) |
| `has_ppr` | bool | ✅ | PPR def 블록 존재 여부 |
| `ppr_file` | str \| null | ❌ | PPR def 소속 파일 (has_ppr=true 시 필수) |
| `ppr_line` | int \| null | ❌ | PPR def 시작 줄 (has_ppr=true 시 필수) |
| `decomposed_to` | str \| null | ❌ | 분리된 트리 파일 경로 (status=decomposed 시 필수) |
| `tags` | list[str] | ✅ | #tag 목록 (빈 list 허용) |

### DecomposedLink 필드

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_node` | str | ✅ | (decomposed) 마킹된 원본 노드명 |
| `source_file` | str | ✅ | 원본 파일 경로 |
| `target_file` | str | ✅ | 분리된 트리 파일 경로 |
| `target_root` | str | ✅ | 분리된 트리의 루트 노드명 |

---

## 3. MANIFEST.json 전체 스키마

```json
{
  "pgxf_version": "1.0",
  "workspace": "WorkspaceName",
  "projects": [
    {
      "name":           "ProjectName",
      "index":          ".pgxf/INDEX-ProjectName.json",
      "design":         ".pgf/DESIGN-ProjectName.md",
      "workplan":       ".pgf/WORKPLAN-ProjectName.md",
      "total_nodes":    24,
      "done":           12,
      "completion_pct": 50.0,
      "status_summary": {
        "done": 12, "in-progress": 5, "designing": 4,
        "blocked": 2, "decomposed": 1
      },
      "blocked_nodes":  ["PaymentGateway"],
      "decomposed_files": [".pgf/DESIGN-PaymentFlow.md"]
    }
  ],
  "global_summary": {
    "total_projects":  3,
    "total_nodes":     88,
    "done":            66,
    "completion_pct":  75.0,
    "status_summary": {
      "done": 66, "in-progress": 12, "designing": 7, "blocked": 3
    }
  },
  "updated_at": "2026-04-11T09:00:00"
}
```

### MANIFEST 프로젝트 엔트리

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | ✅ | 프로젝트명 |
| `index` | str | ✅ | INDEX 파일 경로 |
| `design` | str \| null | ✅ | DESIGN 파일 경로 (없으면 null) |
| `workplan` | str \| null | ❌ | WORKPLAN 파일 경로 |
| `total_nodes` | int | ✅ | 전체 노드 수 |
| `done` | int | ✅ | 완료 노드 수 |
| `completion_pct` | float | ✅ | 완료율 (소수점 1자리) |
| `status_summary` | dict[str, int] | ✅ | 상태별 집계 |
| `blocked_nodes` | list[str] | ❌ | blocked 노드 목록 (빠른 확인용) |
| `decomposed_files` | list[str] | ❌ | decomposed 분리 파일 목록 |

---

## 4. 노드명 유일성 규칙

프로젝트 스코프 내에서 노드명은 유일해야 한다.

### 중복 발생 시 처리

```
[PGXF] ⚠ DUPLICATE NODE: "ValidateCard"
  → .pgf/DESIGN-OrderSystem.md:12
  → .pgf/DESIGN-PaymentFlow.md:4
  Action: 첫 번째를 채택, 두 번째에 경고 마킹
  Fix: 노드명을 OrderValidateCard / PaymentValidateCard로 분리 권장
```

### (decomposed) 예외

`(decomposed)` 노드는 원본 파일과 분리된 파일 양쪽에 동일 이름이 존재한다. 이는 중복이 **아니다** — PGXF가 `decomposed_links`로 연결하고, 원본의 엔트리를 대표로 사용한다.

---

## 5. PPR 매칭 규칙

### CamelCase → snake_case 변환

```
PaymentProcessor    → payment_processor
AI_ExtractKeywords  → ai_extract_keywords  (인라인 — 매칭 불요)
ValidateCard        → validate_card
SeAAIHub           → se_aai_hub
```

### 매칭 우선순위

1. **정확 매칭**: `def payment_processor(` ← `PaymentProcessor`
2. **접두사 매칭**: `def payment_processor_v2(` ← `PaymentProcessor` (경고 출력)
3. **매칭 실패**: `has_ppr = false`

### PPR 위치 탐색 범위

1. 동일 파일의 `## PPR` 섹션 (우선)
2. 동일 프로젝트의 다른 DESIGN 파일
3. 분리된 `(decomposed)` 파일

---

## 6. status 값 매핑

PG 기본 6개 + PGF 확장 3개 = 총 9개 상태:

| Status | Origin | summary 키 |
|--------|--------|------------|
| `done` | PG | `done` |
| `in-progress` | PG | `in-progress` |
| `designing` | PG | `designing` |
| `blocked` | PG | `blocked` |
| `decomposed` | PG | `decomposed` |
| `needs-verify` | PG | `needs-verify` |
| `delegated` | PGF | `delegated` |
| `awaiting-return` | PGF | `awaiting-return` |
| `returned` | PGF | `returned` |

summary 집계에서 `decomposed` 노드는 **total에 포함하되 completion 계산에서 제외**한다 (분리된 트리에서 별도 집계).

---

## 7. Sync Diff 출력 포맷

```json
{
  "added": [
    {"node": "RefundFlow", "file": ".pgf/DESIGN-OrderSystem.md", "line": 22}
  ],
  "removed": [
    {"node": "LegacyGateway", "last_file": ".pgf/DESIGN-OrderSystem.md"}
  ],
  "modified": [
    {
      "node": "ChargeCard",
      "field": "status",
      "old": "designing",
      "new": "in-progress"
    },
    {
      "node": "SendReceipt",
      "field": "line",
      "old": 18,
      "new": 20
    }
  ]
}
```
