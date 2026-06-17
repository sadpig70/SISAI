# DESIGN — SISAI (Self-improvement Security AI) @v:0.1

> A self-improving security AI that **autonomously discovers and expands** security/safety channels,
> collects threats (hacking methods and cases), and **searches externally first → otherwise self-designs via pgf**
> to build detection/prevention defenses. It **records and reuses** channels, threats, and defenses.
> Notation: vendored `skills/{pg,pgf,pgxf}`. Driving engine: AI runtime (parser-free skills).
> Design lineage: HELIX's explore⊕exploit + backbone spiral (pattern only, no code dependency — **fully HELIX-independent**).

---

## 0. Core Thesis

```text
One deterministic backbone (core/) · three strands · self-improvement spiral.
  Strand A (ThreatIntel)  : scan channels → collect and classify threats (attack techniques and cases)
  Strand B (DefenseSynth) : search externally for solutions first → otherwise self-design via pgf
  Strand C (DetectOps)    : operate defenses as detection rules/reports → feed results back into the corpus
The channels themselves are first-class assets: discover → ledger → reuse. The backbone is the single source.
Verified defense → corpus feedback (base pairs) → next turn compounds into better defense synthesis (a spiral without convergence).
```

## 1. Governing Constraints (invariant)

```text
Determinism boundary : core/ is pure stdlib (no clock, network, AI, or RNG; now is injected).
              Collected external text cannot alter core's control flow = first-line prompt-injection defense.
AI meta-layer    : actual channel scanning, threat understanding, and defense design are the AI runtime's (skills) responsibility — outside core.
defensive-only: outputs are detection/prevention/reports. Weaponizing working exploits or automating targeted attacks is out of scope (blocked).
self-contained      : runs from the SISAI folder alone. Zero external paths or HELIX imports.
self-defense  : SISAI itself is a target (injection/poisoning/supply-chain/skill contamination) → it protects its own integrity via
              fingerprint, ledger, provenance, and corpus signing (docs/SELF-DEFENSE.md).
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

## 3. Material Types (programming-level data — pg)

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

## 4. PPR — Core Logic

### 4.1 Channels (expand·record·reuse the channels themselves) — SISAI-specific

```python
# core/sisai_channels.py (deterministic stdlib)
def register_channel(registry: dict, channel: Channel, now: str) -> dict:
    """Register a discovered channel. Deduplicate by fingerprint (guarantees reuse). Deterministic."""
    fp = channel_fingerprint(channel)        # normalized url|kind hash
    if fp in registry["by_fingerprint"]:
        return {"status": "exists", "channel_id": registry["by_fingerprint"][fp]}
    # ... append + index ...
    # criteria: re-registering the same channel is idempotent; preserve the discovery source (discovered_from)

def next_channels_to_scan(registry: dict, coverage: dict, k: int) -> list:
    """Select scan candidates, prioritizing the least-covered kind (avoid skew). Deterministic ordering."""

def should_discover_channels(registry: dict, policy: dict) -> bool:
    """Active channels < floor or a gap in kind coverage → a channel-discovery turn is needed."""
```
> AI meta-layer (skills, in the sdx spirit): actually *discovering* new channels is done by the AI from the web/catalogs →
> the deterministic core *records, deduplicates, and reuses* the result. (HELIX sdx⊕ledger integrated into the backbone)

### 4.2 SolveOrDesign (external first → self-design) — SISAI-specific

```python
def plan_defense(threat: Threat, defense_corpus: list, ledger: dict) -> dict:
    """Decide the solution-sourcing strategy (deterministic). Actual search/design is done by the AI meta-layer."""
    if is_consumed({"title": threat["title"], "fingerprint": threat_fp(threat)}, ledger)["consumed"]:
        return {"action": "SKIP", "why": "threat already defended (reuse)"}
    # 1) Is there an existing defense in the external corpus that applies? (deterministic matching: category/technique overlap)
    hit = match_external_defense(threat, defense_corpus)
    if hit:
        return {"action": "ADOPT_EXTERNAL", "defense": hit,
                "why": "external solution found → adopt + adapt"}
    # 2) If none, self-design (pgf full-cycle handoff)
    return {"action": "DESIGN_DEFENSE", "spec": to_pgf_seed(threat),
            "why": "no external solution → design via pgf"}
    # acceptance_criteria:
    #   - when an external solution exists, always prefer it over self-design
    #   - self-designed defenses are fed back into the corpus only after passing verification
```

### 4.3 Loop (3 strands + triage) — next_action

```python
def next_action(state: dict, policy: dict = None) -> dict:
    """Deterministic. Priority: feedback > channel discovery > threat collection > defense sourcing > balance."""
    if state.get("pending_verified_defense"):
        return {"action": "RECORD_DEFENSE", "why": "verified defense → ledger+corpus (close loop)"}
    if state.get("should_discover_channels"):
        return {"action": "DISCOVER_CHANNELS", "why": "channel coverage low → expand sources"}
    if state.get("untriaged_threats", 0) == 0 and state.get("active_channels", 0) > 0:
        return {"action": "RUN_THREAT_INTEL", "why": "scan channels for fresh threats"}
    top = state.get("top_threat")                       # the highest-priority threat chosen by triage
    if top:
        return {"action": "SOLVE_OR_DESIGN", "why": "address highest-priority threat", "target": top}
    return {"action": "RUN_THREAT_INTEL", "why": "balance → keep sensing"}
```

### 4.4 Triage (severity×recency) — security-specific dimension

```python
def triage_score(threat: Threat, now: str, w=(0.6, 0.4)) -> float:
    """Weighted CVSS (normalized) × recency (more recent → higher) — deterministic. now is injected."""
    sev = (threat.get("cvss") or 0.0) / 10.0
    rec = recency_decay(threat.get("recency"), now)      # 0..1 (linear decay)
    return w[0]*sev + w[1]*rec
def rank_threats(threats: list, now: str) -> list:       # descending; ties broken by threat_id (deterministic)
```

### 4.5 Diversity (attack-surface coverage = blind-spot prevention) — inherited from the HELIX pattern

```python
def measure_coverage(threats: list, thresholds=None) -> dict:
    """Measure blind spots via the category/technique/channel-kind distribution.
       If it skews toward one axis, repair_required=True → the loop steers toward the uncovered axis."""
    # lineage: adapts HELIX diversity's keyword_coverage/repair_required pattern to security axes.
```

## 5. Decisions (finalized as defaults)

| Decision | Adopted value | Rationale |
|---|---|---|
| Operating depth | up to detection rules and report generation (actual blocking is meta-layer/out-of-scope) | defensive; autonomous blocking is risky |
| Protected assets | AI systems, source code, logs (focused on AI-abuse threats) | the seed summary.md covers AI-abuse threats |
| HELIX reuse | vendor (pattern lineage, zero code dependency) | full-independence requirement |
| dual-use | defensive-only (weaponization blocked) | safety boundary |

## 6. Verification Gate (acceptance)

```text
- python -m unittest discover -s tests → OK (deterministic, identical across 2 runs)
- python core/sisai_validate.py . → PASS (structure + seed + schema contract)
- python sisai.py status → channel/threat/defense status + next_action output
- channel register idempotent; SolveOrDesign external-first; defense feedback only after verification
- core: zero clock/RNG/network/AI/HELIX imports (now injected only)
- self-defense: collected text does not alter core control flow (injection-defense test)
```
