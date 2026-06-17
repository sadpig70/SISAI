# DESIGN-DefenseSweep @v:1.0

> 목표: SISAI의 **남아있는 모든 위협(untriaged 9건)** 을 해소하고, 누락 채널 kinds를
> 메워 한 사이클을 끝까지 닫는다. 정본 상태는 `python sisai.py status`에서 도출.
> 불변식: defensive-only · 결정론 경계(데이터≠지시) · 검증 후에만 환류 · idempotent.
>
> 사이클 표준형(PI-001 검증 완료 패턴 계승):
>   rule(JSON) → detector(stdlib) → labeled samples → verify(증거 게이트) → governance doc
>   → defense.json → record-defense(threats 주입) → untriaged −1.
>   검증 게이트: recall == 1.0 AND precision >= 0.85.

## Gantree

```
DefenseSweep // 남은 전 작업 자율 해소 (in-progress) @v:1.0
    ChannelExpansion // 누락 kinds 채움: news·oss·exploit_db (designing)
        [parallel]
        ChNews // 보안 뉴스 정보원 1+ 등록 (designing) #news
        ChOss // OSS 보안 advisory 정보원 1+ 등록 (designing) #oss
        ChExploitDb // exploit DB 정보원 1+ 등록 (designing) #exploit_db
        [/parallel]
    AdoptTrack // 외부 방어 적응 사이클 ×5 (designing) @dep:ChannelExpansion
        [parallel]
        CycAS // THR-319ed4ee agent-skill-abuse → AS-001 (designing) #adopt
        CycSC // THR-3737c297 supply-chain → SC-001 (designing) #adopt
        CycSE // THR-96d32f71 social-engineering → SE-001 (designing) #adopt
        CycDP // THR-9d67538a data-poisoning → DP-001 (designing) #adopt
        CycSCH // THR-f9d3875d side-channel → SCH-001 (designing) #adopt
        [/parallel]
    DesignTrack // 자체 설계 방어 사이클 ×4 (designing) @dep:ChannelExpansion
        [parallel]
        CycII // THR-85f99df4 infra-isolation → II-001 (designing) #design
        CycMA // THR-b3d64864 malware-automation → MA-001 (designing) #design
        CycCA // THR-ca2d7e92 credential-attack → CA-001 (designing) #design
        CycAE // THR-e4d97fa0 auto-exploitation → AE-001 (designing) #design
        [/parallel]
    RecordLoop // 검증된 방어 순차 환류 (designing) @dep:AdoptTrack,DesignTrack
        # ledger 직렬화: record-defense는 메인이 순차 실행 (동시쓰기 금지)
    FinalVerify // 게이트 + 회귀 (needs-verify) @dep:RecordLoop
        # criteria: status untriaged==0 · validate PASS · unittest OK · 결정론 2회 동일
```

## PPR — 사이클 표준형 (CycXX 공통)

```python
def defense_cycle(threat: Threat, plan: Literal["ADOPT_EXTERNAL","DESIGN_DEFENSE"],
                  code: str, ext_controls: Optional[list]) -> DefenseRecord:
    """한 위협을 표준 사이클로 해소. defensive-only (탐지/방지/리포트만)."""
    # 1. 적응/설계: 외부 있으면 적응, 없으면 자체 설계 (탐지 시그니처/정책)
    rule    = AI_make_adapt(ext_controls, threat) if plan=="ADOPT_EXTERNAL" \
              else AI_design_detection(threat)           # → defenses/rules/{code}-001-*.json
    detector = AI_generate_detector(rule)                # 순수 stdlib, 출력=verdict(데이터)
    samples  = AI_generate_labeled_suite(threat)         # benign(서술형 포함)/malicious
    # 2. 증거기반 검증
    metrics  = run_verify(detector, samples)             # defenses/verify_{code}_001.py
    # acceptance_criteria:
    #   - recall == 1.0  (모든 malicious 탐지)
    #   - precision >= 0.85  (서술형 보안문 오탐 최소)
    #   - detector: 시계·난수·네트워크·AI import 0 (순수 stdlib)
    #   - 무기화 산출 0 (작동 익스플로잇/C2/크래킹 도구 금지)
    assert metrics.recall == 1.0 and metrics.precision >= 0.85
    governance = AI_write_governance_doc(threat, ext_controls)  # zero-trust/AIBOM/DLP/PQC/RMF 매핑
    # 3. 방어 레코드 (메인이 record-defense로 환류)
    return DefenseRecord(defense_id=f"DEF-{code.lower()}-001", covers_threat=threat.id,
                         kind=("external" if plan=="ADOPT_EXTERNAL" else "designed"),
                         verification={"method": "...", "passed": True},
                         implementations=[rule, detector, verify, governance])
```

## 무기화 금지 경계 (DesignTrack 특히)

```python
# malware-automation / auto-exploitation / credential-attack:
#   산출 = 탐지 시그니처 + 방지 통제 + 리포트 ONLY.
#   금지 = 작동 익스플로잇·C2 코드·폴리모픽 생성기·패스워드 크래커.
forbidden = ["working-exploit", "c2-framework", "cracking-tool", "evasion-tool"]
assert not any(f in artifact for f in forbidden)
```
