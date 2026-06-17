# DESIGN — SISAI (Self-improvement Security AI) @v:0.1

> 보안/안전 채널을 **스스로 발굴·확장**하며 위협(해킹 방법·사례)을 수집하고,
> 해결책을 **외부에서 우선 탐색 → 없으면 pgf로 자체 설계**해, 감지/방지 방어를
> 만들어 가는 자기개선 보안 AI. 채널·위협·방어를 **기록하고 재사용**한다.
> 표기: vendored `skills/{pg,pgf,pgxf}`. 구동 엔진: AI 런타임(parser-free skills).
> 설계 계승: HELIX의 explore⊕exploit+백본 나선 (코드 의존 없이 패턴만 — **HELIX 완전 독립**).

---

## 0. 핵심 명제

```text
하나의 결정론 백본(core/) · 세 가닥 · 자기개선 나선.
  가닥 A (ThreatIntel)  : 채널 스캔 → 위협(공격기법·사례) 수집·분류
  가닥 B (DefenseSynth) : 해결책 외부 탐색 우선 → 없으면 pgf 자체 설계
  가닥 C (DetectOps)    : 방어를 탐지 규칙/리포트로 운영 → 성과를 코퍼스로 환류
채널 자체가 1급 자산: 발굴(discover)→기록(ledger)→재사용(reuse). 백본이 단일 출처.
검증된 방어 → 코퍼스 환류(염기쌍) → 다음 턴이 복리로 더 나은 방어 합성 (수렴 없는 나선).
```

## 1. 지배 제약 (불변)

```text
결정론 경계  : core/ 는 순수 stdlib(시계·네트워크·AI·난수 없음; now 주입).
              수집된 외부 텍스트는 core의 제어 흐름을 바꿀 수 없다 = 프롬프트 인젝션 1차 방어.
AI 메타층    : 실제 채널 스캔·위협 이해·방어 설계는 AI 런타임(skills) 책임 — core 밖.
defensive-only: 산출은 탐지/방지/리포트. 작동 익스플로잇 무기화·표적공격 자동화는 범위 밖(차단).
자기완결      : SISAI 폴더만으로 구동. 외부 경로·HELIX import 0.
self-defense  : SISAI 자신이 표적(인젝션/포이즈닝/공급망/스킬오염) → fingerprint·ledger·
              provenance·코퍼스 서명으로 자기 무결성 보호 (docs/SELF-DEFENSE.md).
```

## 2. System Gantree

```text
SISAI // self-improvement security AI (designing) @v:0.1
    SisaiCore // deterministic shared backbone, stdlib only (designing)
        Fingerprint // threat/defense/channel identity primitives (designing)
        Channels // ★ channel registry — discover·record·reuse (designing)
        Ledger // processed-threat / built-defense reuse gate (designing)
        Diversity // attack-surface coverage = blind-spot guard (designing)
        Triage // severity×recency priority policy (designing)
        Provenance // threat→defense lineage + verified-defense→corpus feedback (designing)
        Loop // next_action over the 3 strands (designing)
        Io // atomic crash-safe JSON writes (designing)
        Schema // stdlib JSON-Schema-subset contract checker (designing)
        Validate // structure + contract validator (designing)
    SisaiEngines // strand adapters: native artifacts → backbone (designing)
        ThreatAdapter // collected threats → backbone (designing)
        DefenseAdapter // external/synthesized defenses → backbone (designing)
        ChannelAdapter // discovered channels → registry (designing)
    Driver // sisai.py — status / discover / record / loop-status (designing)
    Skills // vendored pg/pgf/pgxf (AI-native engine) (done)
    Schemas // threat/defense/channel/ledger/loop-state contracts (designing)
    Seed // taxonomy+defenses+channels from the AI-abuse summary (designing)
    Docs // README/RUNBOOK/ARCHITECTURE/SELF-DEFENSE/INSTRUCTIONS (designing)
    Examples // sample state fixtures (designing)
    Tests // deterministic unittests (designing)
```

## 3. 자재 타입 (programming-level data — pg)

```python
Channel  = dict = {"id": str, "kind": Literal["cve","advisory","news","paper","oss","exploit_db","vendor_intel","standard"],
                   "url": str, "discovered_from": str, "orthogonality": float, "status": Literal["active","stale"]}
Threat   = dict = {"threat_id": str, "title": str, "category": str, "techniques": list[str],
                   "cve": Optional[str], "cvss": Optional[float], "recency": str,  # injected date
                   "source_channels": list[str], "evidence": list[str]}
Defense  = dict = {"defense_id": str, "title": str, "kind": Literal["external","designed"],
                   "controls": list[str], "covers_threat": str, "origin": str,
                   "provenance": list[dict], "verification": dict, "implementations": list[dict]}
LedgerEntry = dict = {"entry_id": str, "kind": Literal["threat","defense","channel"],
                      "title": str, "fingerprint": str, "implementations": list[dict]}
```

## 4. PPR — 핵심 로직

### 4.1 Channels (채널 자체를 확장·기록·재사용) — SISAI 고유

```python
# core/sisai_channels.py (결정론 stdlib)
def register_channel(registry: dict, channel: Channel, now: str) -> dict:
    """발굴한 채널을 등록. fingerprint로 중복 차단(재사용 보장). 결정론."""
    fp = channel_fingerprint(channel)        # url|kind 정규화 해시
    if fp in registry["by_fingerprint"]:
        return {"status": "exists", "channel_id": registry["by_fingerprint"][fp]}
    # ... append + index ...
    # criteria: 같은 채널 재등록 idempotent; 발굴 출처(discovered_from) 보존

def next_channels_to_scan(registry: dict, coverage: dict, k: int) -> list:
    """커버리지 최소 kind를 우선해 스캔 후보 선정 (편중 방지). 결정론 정렬."""

def should_discover_channels(registry: dict, policy: dict) -> bool:
    """활성 채널 < floor 또는 kind 커버리지 구멍 → 채널 발굴 turn 필요."""
```
> AI 메타층(skills, sdx 정신): 실제 새 채널 *발견*은 AI가 웹/카탈로그에서 수행 →
> 결정론 core는 그 결과를 *기록·중복차단·재사용*한다. (HELIX sdx⊕ledger를 백본으로 통합)

### 4.2 SolveOrDesign (외부 우선 → 자체 설계) — SISAI 고유

```python
def plan_defense(threat: Threat, defense_corpus: list, ledger: dict) -> dict:
    """해결책 조달 전략 결정 (결정론). 실제 탐색/설계는 AI 메타층이 수행."""
    if is_consumed({"title": threat["title"], "fingerprint": threat_fp(threat)}, ledger)["consumed"]:
        return {"action": "SKIP", "why": "threat already defended (reuse)"}
    # 1) 외부 코퍼스에 적용 가능한 기존 방어가 있나? (결정론 매칭: category/technique 겹침)
    hit = match_external_defense(threat, defense_corpus)
    if hit:
        return {"action": "ADOPT_EXTERNAL", "defense": hit,
                "why": "external solution found → adopt + adapt"}
    # 2) 없으면 자체 설계 (pgf full-cycle 핸드오프)
    return {"action": "DESIGN_DEFENSE", "spec": to_pgf_seed(threat),
            "why": "no external solution → design via pgf"}
    # acceptance_criteria:
    #   - 외부 해결책 존재 시 자체설계보다 항상 외부 우선
    #   - 자체 설계분은 검증 통과 후에만 코퍼스 환류
```

### 4.3 Loop (3가닥 + triage) — next_action

```python
def next_action(state: dict, policy: dict = None) -> dict:
    """결정론. 우선순위: 환류 > 채널발굴 > 위협수집 > 방어조달 > 균형."""
    if state.get("pending_verified_defense"):
        return {"action": "RECORD_DEFENSE", "why": "verified defense → ledger+corpus (close loop)"}
    if state.get("should_discover_channels"):
        return {"action": "DISCOVER_CHANNELS", "why": "channel coverage low → expand sources"}
    if state.get("untriaged_threats", 0) == 0 and state.get("active_channels", 0) > 0:
        return {"action": "RUN_THREAT_INTEL", "why": "scan channels for fresh threats"}
    top = state.get("top_threat")                       # triage가 고른 최우선 위협
    if top:
        return {"action": "SOLVE_OR_DESIGN", "why": "address highest-priority threat", "target": top}
    return {"action": "RUN_THREAT_INTEL", "why": "balance → keep sensing"}
```

### 4.4 Triage (severity×recency) — 보안 고유 차원

```python
def triage_score(threat: Threat, now: str, w=(0.6, 0.4)) -> float:
    """CVSS(정규화) × recency(최근일수록 ↑) 가중 — 결정론. now 주입."""
    sev = (threat.get("cvss") or 0.0) / 10.0
    rec = recency_decay(threat.get("recency"), now)      # 0..1 (선형 decay)
    return w[0]*sev + w[1]*rec
def rank_threats(threats: list, now: str) -> list:       # 내림차순, 동점은 threat_id (결정론)
```

### 4.5 Diversity (공격표면 커버리지 = 사각지대 방지) — HELIX 패턴 계승

```python
def measure_coverage(threats: list, thresholds=None) -> dict:
    """카테고리/technique/channel-kind 분포로 사각지대(blind spot) 측정.
       특정 축으로 쏠리면 repair_required=True → loop가 미커버 축으로 조향."""
    # 계승: HELIX diversity의 keyword_coverage/repair_required 패턴을 보안 축으로.
```

## 5. 결정 사항 (기본값으로 확정)

| 결정 | 채택값 | 근거 |
|---|---|---|
| 운영 깊이 | 탐지 규칙·리포트 생성까지 (실차단은 메타층/범위밖) | defensive, 자율 차단은 위험 |
| 보호 대상 | AI 시스템·소스코드·로그 (AI-abuse 위협 중심) | seed 요약.md가 AI 악용 위협 |
| HELIX 재사용 | vendor(패턴 계승, 코드 의존 0) | 완전 독립 요구 |
| dual-use | defensive-only (무기화 차단) | 안전 경계 |

## 6. 검증 게이트 (acceptance)

```text
- python -m unittest discover -s tests → OK (결정론 2회 동일)
- python core/sisai_validate.py . → PASS (구조 + seed + 스키마 계약)
- python sisai.py status → 채널/위협/방어 상태 + next_action 출력
- 채널 register idempotent; SolveOrDesign 외부우선; 방어 환류는 검증 후에만
- core: 시계·난수·네트워크·AI·HELIX import 0 (now 주입만)
- self-defense: 수집 텍스트가 core 제어흐름 불변 (인젝션 방어 테스트)
```
