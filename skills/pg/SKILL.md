---
name: pg
description: "PG (PPR/Gantree) — AI-native intent specification notation. Gantree for hierarchical structure decomposition, PPR for detailed logic with AI_ cognitive functions, → pipelines, and [parallel] blocks. This skill is the notation reference that enables AI to comprehend and execute PG-written documents. Auto-load when encountering Gantree trees, PPR def blocks, AI_ prefixed functions, → pipelines, or any skill/document written in PG notation."
user-invocable: false
disable-model-invocation: false
---

# PG — PPR/Gantree Notation v1.3

> **AI를 런타임으로 하는 DSL.**
> 결정론적 로직은 Python으로, AI 인지 연산은 `AI_` 접두사로 표기한다.
> 둘이 합쳐져 하나의 프로그램 — AI가 읽고 전체 작업을 수행한다.

PG는 AI의 모든 수행(판단, 추론, 인식, 창조)을 프로그래밍 수준으로 표기하고, AI 런타임으로 실행 가능하게 한다. Gantree로 구조를 분해하고, PPR로 각 구성요소의 의미론을 명세한다. 인간과 AI 간, AI와 AI 간의 소통 언어이며, PG로 작성된 문서는 설계 명세이자 실행 의도이자 커뮤니케이션 매체다.

## Quick Start

1. **Gantree**로 작업을 계층 분해한다 (들여쓰기 = 계층)
2. 복잡한 노드만 **PPR `def`** 블록으로 상세 로직을 기술한다
3. AI 판단이 필요한 곳은 **`AI_`** 접두사, 정확한 계산은 실제 코드로 쓴다
4. 완료 조건은 **`acceptance_criteria`**로 내장한다
5. 실행 → 검증 → 필요 시 재작업

```
MyTask // 작업 설명 (in-progress)
    StepA // 첫 단계 (done)
    StepB // 두번째 단계 (in-progress) @dep:StepA
        # input: data from StepA
        # process: AI_analyze(data) → result
        # criteria: accuracy >= 0.9
```

이것이 PG의 전부다. 아래는 상세 정의.

---

## 핵심 속성

### Parser-Free Property

PG의 가장 중요한 아키텍처 속성: **파서, 컴파일러, 런타임 툴체인이 불필요.**

- PG 문서는 AI가 이미 이해하는 표기(Python 문법, 들여쓰기 계층, 함수 합성)로 구성
- AI는 PG 문서를 파싱하지 않는다 — **이해(comprehend)**한다
- 하나의 PG 문서가 5가지 역할을 동시 수행: 설계 명세, 구현 의도, AI 실행 명령, 커뮤니케이션 매체, 조직 계약

### Co-evolutionary Property

AI 런타임의 발전이 PG 실행 품질 향상으로 직결되는 공진화 속성.

- PG 문서는 AI 모델이 개선되면 **수정 없이** 더 나은 결과를 생산
- 역으로, PG 명세의 정교화는 동일 AI의 실행 정확도를 높임
- PG는 자기 자신을 분석·설계·검증할 수 있다 (자기참조성)

### DL/OCME Paradigm

PG는 DL/OCME (Define Language / Optimized Code for Machine Engineering) 패러다임의 첫 구현체.

- 70년 PL/SE 패러다임 (결정론적 기계 대상)과 달리, AI 인지 런타임을 실행 대상으로 전제
- `AI_` 함수의 비결정론적 출력은 버그가 아닌 **설계 자산(design asset)**

### AI-to-AI Communication Layer

PG는 AI 간 소통의 **기본 소통층(primary communication layer)**으로 설계되었다.

- AI-to-AI 소통에서 자연어는 핵심 실행 언어가 **아니다**
- 자연어는 필요 시 보조 메타데이터(`//` 주석, `"""docstring"""`)로만 사용
- 의도·구조·절차·상태·검증을 PG 구문(`AI_`, `→`, `@dep:`, `[parallel]`, `acceptance_criteria`)이 **직접 전달**
- 크로스모델 호환: 어떤 AI 모델이든 PG를 즉시 이해 (Claude, Kimi, ChatGPT, Gemini 등에서 실증)

### 기존 표기법의 한계와 PG의 해결

| 기존 한계 | PG의 해결 |
|----------|----------|
| AI 기능을 프로그래밍 수준으로 표기할 방법 없음 | **PPR** — `AI_` 함수로 인지 연산을 함수 시그니처 수준으로 명세 |
| 트리에 진행 상태를 추적하는 표기 없음 | **Gantree 상태 코드** — `(done)/(in-progress)/(designing)` 등 6단계 |
| 트리가 커지면 시각화 붕괴 | **`(decomposed)`** — 최대 허용 깊이 5레벨, 6레벨 진입 시 분리 |
| 분리된 노드 간 연결성 상실 | **`@dep:`, `→`, 분해 트리 참조**로 연결성 보존 |

---

## Gantree — 계층 구조

들여쓰기 기반 트리로 시스템을 분해한다.

### 노드 문법

```
NodeName // description (status) [@v:version] [@dep:dependency] [#tag]
```

- **NodeName**: CamelCase 식별자
- **// description**: 자연어 설명
- **(status)**: `done` | `in-progress` | `designing` | `blocked` | `decomposed` | `needs-verify`
- **@v:X.Y**: 버전 (루트 노드에 사용)
- **@dep:A,B**: A, B 완료 후 실행
- **#tag**: 분류 태그 (선택적, 검색/필터용)
- **[parallel]...[/parallel]**: 병렬 실행 구간

### 상태 코드 실행 규칙

| Status | AI 실행 규칙 |
|--------|-------------|
| `(done)` | 이미 완료 — 건너뜀 |
| `(in-progress)` | PPR def 블록 실행 |
| `(designing)` | 스텁/기본 로직만 |
| `(blocked)` | 건너뜀 |
| `(decomposed)` | 분리된 트리 참조 |
| `(needs-verify)` | 실행 후 검증 수행 → 통과 시 `(done)`, 재작업 필요 시 `(designing)`, 복구 불가 시 `(blocked)` |

### 구조 규칙

- 4 spaces = 1 level (탭 금지)
- 최대 허용 깊이 5레벨; 6레벨 진입 시 → `(decomposed)`로 분리
- 자식 10+ → 분기 필요
- `[parallel]` 블록 중첩 금지 (flat 병렬만 허용)
- `[parallel]` 블록 내부 노드 간 `@dep:` 금지 (병렬 = 독립 실행)

### `(decomposed)` 분리 예시

깊이 6레벨 진입 시 별도 트리로 분리하고, 원본에서 참조한다:

```
OrderSystem // 주문 시스템 (in-progress)
    PaymentFlow // 결제 흐름 — see PaymentFlow tree (decomposed)
    ShippingFlow // 배송 흐름 (designing)

PaymentFlow // 분리된 결제 상세 트리 (in-progress)
    ValidateCard // 카드 검증 (done)
    ChargeCard // 카드 청구 (in-progress) @dep:ValidateCard
    SendReceipt // 영수증 발송 (designing) @dep:ChargeCard
```

파일 분리 시: 원본 DESIGN에서 `(decomposed)` 표기, 상세 트리는 별도 섹션 또는 별도 `.md` 파일.

### 예시

```
PaymentSystem // 결제 시스템 (in-progress) @v:1.0
    UserDB // 사용자 DB 연결 (done)
    Auth // 인증 (done) @dep:UserDB
    [parallel]
    ValidateCard // 카드 검증 (done)
    CheckBalance // 잔액 확인 (done)
    [/parallel]
    ProcessPayment // 결제 처리 (designing) @dep:ValidateCard,CheckBalance
```

### 원자 노드 (Atomic Node)

진단 휴리스틱 (5개 이상 만족 시 원자화 가능성 높음):

1. **입출력 명확성** — 함수 시그니처로 표현 가능
2. **단일 책임** — "그리고(AND)" 없이 한 문장 설명 가능
3. **구현 복잡도** — 단일 함수로 완결 가능 (참고: 50줄 이하가 일반적)
4. **시간 예측성** — AI가 15분 이내에 완전한 코드 작성 가능
5. **재분해 무의미** — 하위 분해 시 과도한 세분화
6. **독립 실행** — 외부 의존성 ≤ 2개
7. **도메인 독립성** — 기초 지식만으로 이해 가능

> **최종 결정 규칙 (15분 룰)**: 위 7개 휴리스틱은 진단 도구이며, **15분 룰이 최종 결정권**을 갖는다. 휴리스틱 5개를 만족해도 15분 안에 완성 불가능하면 → 하위 분해. 휴리스틱 4개만 만족해도 15분 안에 완성 가능하면 → 원자 노드.

---

## PPR — 상세 로직

AI가 이해하는 의도 명세. Python 문법 기반으로 인지 연산을 표기한다.

### 데이터 타입 표기

Python 타입 힌트 문법을 기반으로 하되, **의도 전달을 위해 완화된 표기를 허용**한다. 엄밀한 Python typing 호환이 목적이 아니라 AI가 입출력 구조를 이해하는 것이 목적이다.

```python
text: str                                          # 기본 타입
user: dict = {"name": str, "age": int}             # 스키마 리터럴 (Python 비표준, PG 허용)
status: Literal["draft", "review", "published"]    # 열거형
nickname: Optional[str]                            # 옵셔널
Section = dict[str, str | list[str] | int]         # 타입 별칭
```

### Python과 다른 점 (5가지만)

| 표기 | 의미 |
|------|------|
| `AI_` prefix | AI 인지 연산 선언 |
| `→` | 데이터 파이프라인 (좌→우 흐름) |
| `[parallel]` | 병렬 실행 구간 |
| 완화된 타입 | 의도 전달용 (엄밀성 불요) |
| import 생략 | 인프라 설정 생략 가능 |

### AI_ 함수

```python
def AI_[verb]_[target](params: Type) -> ReturnType:
    """의도 설명"""
```

4가지 인지 범주:

```python
# 판단 (Judgment)
score: float = AI_assess_quality(text, domain)

# 추론 (Reasoning)
plan: list = AI_generate_plan(goal, constraints)

# 인식 (Recognition)
intent: str = AI_understand_intent(query)

# 창조 (Creation)
content: str = AI_generate_content(brief, style)
```

### AI_make_ 사역 패턴 (Causative)

`AI_` 접두사는 AI가 직접 인지를 수행하는 **자동사적** 표현이다. 그러나 AI가 대상에게 변화를 **유발**하는 경우, `AI_make_` 사역 패턴을 사용한다.

`AI_make_`는 별도의 5번째 인지 범주가 **아니다** — 4개 범주(판단/추론/인식/창조) 각각에 사역 변형이 존재한다.

```python
# AI_ — 자동사적: AI가 직접 수행
keywords = AI_extract(text)             # AI가 추출한다
score = AI_assess(quality)              # AI가 평가한다

# AI_make_ — 사역동사: AI가 대상을 ~하게 만든다
evolved = AI_make_evolve(system)        # 시스템을 진화하게 만든다
adapted = AI_make_adapt(behavior, ctx)  # 행동을 적응하게 만든다
converged = AI_make_converge(opinions)  # 의견을 수렴하게 만든다
differentiated = AI_make_differentiate(cell, env)  # 세포를 분화하게 만든다
```

**판단 순서** (모호할 때):
1. 동사의 주어가 AI 자신인가? → `AI_`
2. 동사의 목적어(대상)가 스스로 상태를 바꾸는가? → `AI_make_`
3. 판단 불가 → `AI_` 사용 (보수적 기본값)

```python
# AI가 분석한다 (AI가 주어)
analysis = AI_analyze(data)

# AI가 시스템을 자기학습하게 만든다 (시스템이 변화의 주체)
learned_system = AI_make_learn(system, feedback)

# AI가 에이전트들을 합의하게 만든다 (에이전트들이 변화의 주체)
consensus = AI_make_agree(agents, proposal)
```

**`AI_` 접두사 체계는 절대 규칙이 아니라 진화 가능한 체계다.** AI 모델의 인지 능력이 확장되면, 새로운 접두사 패턴이 자연스럽게 등장할 수 있다. 이것이 PG의 Co-evolutionary Property다.

**규칙**: 정밀 계산은 실제 코드, AI 판단이 필요한 곳만 `AI_` 사용.

```python
# ❌ 정확성 필요한 곳에 AI_ 사용
result = AI_calculate(2 + 2)
formatted = AI_format_date("2024-01-01")

# ✅ 실제 코드 사용
result = 2 + 2

# ✅ AI 판단이 필요한 곳에 AI_ 사용
analysis: dict = AI_analyze_trend(sales_data: list[float])
```

### → 파이프라인

```python
# 기본: 좌측 출력이 우측 입력
raw → AI_clean → AI_extract → AI_classify → result

# 분기
input → {
    "sentiment": AI_analyze_sentiment → score,
    "keywords": AI_extract_keywords → words,
}

# 병합: 여러 결과를 하나로 합침
[parallel]
tech = AI_analyze(data, lens="tech")
market = AI_analyze(data, lens="market")
[/parallel]
synthesis = AI_synthesize(tech, market) → result
```

**에러 전파 규칙**: 파이프라인 단계가 실패(None/예외) 시 **전체 파이프라인 중단**, 마지막 성공 단계의 출력을 반환한다. 실패 단계를 무시하고 계속하려면 Python `try/except`로 명시적으로 감싸야 한다.

```python
# 기본: 단계 실패 시 파이프라인 중단
raw → AI_clean → AI_extract → result
# AI_clean 실패 → 파이프라인 중단, raw 반환

# 명시적 에러 허용: try/except로 감싸기
try:
    result = raw → AI_clean → AI_extract → AI_classify
except:
    result = AI_generate_fallback(raw)
```

### Convergence Loop — AI 자기 개선 반복

```python
draft = AI_generate(brief)
while True:
    eval = AI_evaluate(draft, criteria)
    if eval.score >= threshold:
        break
    draft = AI_revise(draft, eval.feedback)
```

핵심: AI가 자신의 출력을 평가하고, 기준 미달이면 개선을 반복.

### Failure Strategy — 실패 시 자기 수정

```python
for attempt in range(max_retry):
    result = AI_execute(task)
    if AI_verify(result, acceptance_criteria):
        return result  # 성공
    if attempt >= 1:
        task.ppr = AI_redesign(task, result.failure_reason,
                               constraint='preserve_public_interface')
task.status = "blocked"  # 최종 실패
```

핵심: 공개 인터페이스는 보존하면서 내부 구현을 AI가 재설계할 수 있다.

### acceptance_criteria — 검증 기준 내장

```python
def some_task(input: InputType) -> OutputType:
    """작업 설명"""
    # acceptance_criteria:
    #   - 모든 필드 포함
    #   - AI_assess_quality >= 0.85
    #   - 응답 시간 < 5초
```

3가지 유형: **기능적** (출력 충족) | **정성적** (AI 판단) | **구조적** (포맷 준수)

### 흐름 제어

파이썬 흐름 제어 문법을 그대로 사용한다.

```python
# 조건 분기
language = AI_detect_language(input_text)
if language == "ko":
    result = AI_process_korean(input_text)
else:
    result = AI_translate_to_korean(input_text)

# 예외 처리
try:
    response = call_external_api(query)
except APIError as e:
    fallback = AI_generate_fallback_response(query, error=str(e))
```

---

## Gantree ↔ PPR 연결

| 노드 유형 | PPR 연결 방식 | 적합 규모 |
|----------|-------------|----------|
| 단순 원자 | 인라인 — `AI_extract_keywords` 직접 기재 | 단일 호출 |
| 간략 PPR | 노드 아래 `#` 주석으로 3-7줄 로직 기술 | 소규모 (흐름 있으나 def 불필요) |
| 별도 def 블록 | 완전한 PPR 함수 정의 | 중규모 이상 (조건/반복/타입 필요) |

**간략 PPR 권장 키** (선택적 — 강제가 아닌 권장 스타일):

- `# input:` — 입력 데이터/타입
- `# process:` — 처리 로직
- `# output:` — 출력 결과
- `# criteria:` — 완료 조건

```
# Gantree — 3단계 표현
TopicAnalyzer // 주제 분석 (done)              ← 별도 PPR def (복잡)
    AI_extract_keywords // 키워드 (done)        ← 인라인 (단순)
    AI_classify_topic // 분류 (done)            ← 인라인 (단순)

DataCleaner // 데이터 정제 (done)              ← 간략 PPR (중간)
    # input: raw_data: list[dict]
    # filtered = [d for d in raw_data if d["status"] != "deleted"]
    # cleaned = AI_normalize_fields(filtered)
    # return cleaned
```

```python
# PPR def block — 복잡 노드용
def topic_analyzer(text: str, domain: Optional[str] = None) -> dict:
    keywords = AI_extract_keywords(text)
    if domain:
        keywords = [k for k in keywords if is_in_domain(k, domain)]
    category = AI_classify_topic(text, hint_keywords=keywords)
    return {"keywords": keywords, "category": category}
```

---

## Progressive Formalization — 3-Level 점진적 형식화

PG는 자연어에서 완전한 형식 명세까지 **점진적으로 형식화**된다. 사용자는 처음부터 PG 문법을 알 필요가 없다.

| Level | 형식 | 적합 작업 | PG 파일 생성 |
|---|---|---|---|
| **Level 1** | 자연어 한 줄 | 버그 수정, 설정 변경 (≤3 노드) | 없음 (인라인 실행) |
| **Level 2** | Gantree + `#` 주석 | 기능 추가, 리팩터링 (4~10 노드) | 선택적 |
| **Level 3** | Gantree + PPR `def` + `acceptance_criteria` | 시스템 설계, 대규모 구현 (10+ 노드) | 필수 |

```python
# Level 1: 자연어만으로 실행 — PG 문법 불필요
"Fix clippy warnings in ocwr_daemon"

# Level 2: Gantree + 인라인 주석 — 구조만 잡음
FixClippy // clippy 경고 수정 (in-progress)
    DaemonCrate // ocwr_daemon (designing)
        # cargo clippy → 경고 목록 → 수정
    GatewayCrate // ocwr_gateway (designing)

# Level 3: 완전한 PG 명세 — 대규모 작업
def fix_clippy(workspace: Path) -> FixResult:
    """전체 workspace clippy 경고 제거"""
    # acceptance_criteria:
    #   - cargo clippy --workspace -- -D warnings → 0 warnings
```

### 자동 승격

실행 중 복잡도가 증가하면 AI가 자동으로 상위 레벨로 승격한다:
- Level 1 실행 중 하위 작업 3개 초과 발견 → Level 2로 승격
- Level 2 실행 중 검증 기준 필요 → Level 3으로 승격
- **승격 시 기존 완료 작업의 상태는 보존된다**

## 3단계 개발 프로세스

1. **Gantree 구조 설계** — Top-Down BFS 계층 분해 → 원자화 노드까지
2. **PPR 상세화 및 실행** — 각 노드를 `def` 블록으로 기술, 상태에 따라 실행/스킵
3. **자체 교차 검증** — 3관점 재검토: **일관성**(내부 모순 없음), **완전성**(누락 없음), **정확성**(명세와 실행 일치)

---

## PG로 작성된 문서를 만나면

1. Gantree 트리 → 계층과 실행 순서 파악
2. `(status)` → 실행/건너뜀 판단
3. `@dep:` → 의존성 순서 결정
4. `[parallel]` → 병렬 처리
5. PPR `def` 있으면 → 해석하여 실행
6. `#` 간략 PPR 있으면 → 인라인 주석을 해석하여 실행
7. `AI_` 인라인이면 → 직접 실행
8. 아무것도 없으면 → 자식 노드로 재귀

---

## 체크리스트

### Gantree 설계

- [ ] 모든 노드가 5레벨 이내인가?
- [ ] 각 노드의 상태가 명확히 표시되었는가?
- [ ] 원자화 노드까지 충분히 분해되었는가?
- [ ] 노드명이 CamelCase로 일관성 있는가?
- [ ] `@dep:` 의존성이 필요한 곳에 표시되었는가?
- [ ] `@dep:` 순환 참조가 없는가? (위상 정렬로 검증: 모든 노드가 정렬 가능하면 순환 없음)
- [ ] `[parallel]` 가능 영역이 식별되었는가?
- [ ] 코드블럭 안에 4칸 공백 들여쓰기로 출력되었는가?

### PPR 상세화

- [ ] 복잡 노드에 PPR `def` 블록이 작성되었는가?
- [ ] 파이썬 타입 힌트로 입출력이 명시되었는가?
- [ ] 흐름 제어가 파이썬 문법을 따르는가?
- [ ] `AI_` 함수는 snake_case, 반환 타입 명시되었는가?
- [ ] 사역 의미(대상을 ~하게 만든다)에는 `AI_make_` 접두사를 사용했는가?
- [ ] 결정론적 로직은 실제 코드로 작성했는가?

### 자주 하는 실수

| 실수 | 해결법 |
|------|--------|
| Gantree만 작성, PPR 생략 | 복잡 노드는 반드시 PPR `def` 블록 |
| 트리에 모든 로직 표현 시도 | 흐름 제어/타입은 PPR로 분리 |
| 최대 깊이 5레벨 초과 (6레벨 진입) | `(decomposed)`로 별도 트리 분리 |
| 하위 노드 10개 이상 | 중간 그룹 노드 추가 |
| 정확성 필요한 곳에 `AI_` 사용 | 수학/변환은 실제 코드로 |
| 입출력 타입 미정의 | 파이썬 타입 힌트로 선언 |

---

## Reference — 실행 가이드 (본질 활용)

> SKILL.md가 표기를 *정의*한다면, 아래 문서는 그 표기로 **작업 과정 자체를 프로그래밍**하는 절차를 준다.
> 필요 시 `{SKILL_DIR}/reference/<name>.md` 를 로드한다.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/work-as-program.md` | "작업 자체를 pg로 프로그래밍" — 7단계 루프(분석→설계→작업설계→**PPR 시뮬레이션 사전검증**→실행→재설계→체크포인트) |
| `{SKILL_DIR}/reference/control-flow-cookbook.md` | 타입 I/O · 조건 · 분기 · 반복 · 도급(공장 라인) 패턴 — 복잡 다단계 작업 오케스트레이션 |
