# WORKPLAN-DefenseSweep @v:1.0

> 설계: `.pgf/DESIGN-DefenseSweep.md`. 남은 위협 9 + 누락 채널 3을 자율 해소.
> 표준 사이클 게이트: recall==1.0 AND precision>=0.85. defensive-only.

## POLICY
```yaml
preserve_determinism: true        # detector/core 순수 stdlib (now 주입)
defensive_only: true              # 무기화 산출 차단 (특히 DesignTrack)
verify_each: true                 # 사이클마다 증거기반 verify 통과 필수
ledger_serialized: true           # record-defense는 메인 순차 (동시쓰기 금지)
max_verify_cycles: 2
parallel_dispatch: true           # 산출물 생성은 위협별 병렬 (파일 충돌 없음)
```

## 배치 (의존 순서)
```text
B0 ChannelExpansion   (designing)            news·oss·exploit_db 채널 등록 (discover-channel ×3, dedup)
B1 AdoptTrack         (designing) @dep:B0     5 사이클 병렬: AS·SC·SE·DP·SCH (외부 적응)
B2 DesignTrack        (designing) @dep:B0     4 사이클 병렬: II·MA·CA·AE (자체 설계, 무기화 금지)
B3 RecordLoop         (designing) @dep:B1,B2  검증된 방어 9건 순차 record-defense (threats 주입)
B4 FinalVerify        (needs-verify) @dep:B3  status untriaged==0 · validate · unittest · 결정론 2회
B5 Commit             (designing) @dep:B4     defenses/ + .pgf/ 커밋 (main)
```

## 위협 ↔ 코드 ↔ 방어 매핑
```text
ADOPT  AS  THR-319ed4ee  agent-skill-abuse    <- AI agent least privilege (zero trust)
ADOPT  SC  THR-3737c297  supply-chain         <- Supply-chain & runtime defense (AIBOM)
ADOPT  SE  THR-96d32f71  social-engineering   <- Security culture & workforce
ADOPT  DP  THR-9d67538a  data-poisoning       <- Secret-leak & external-LLM upload control
ADOPT  SCH THR-f9d3875d  side-channel         <- Crypto agility & PQC adoption
DESIGN II  THR-85f99df4  infra-isolation      <- pgf self-design (tenant-escape 탐지)
DESIGN MA  THR-b3d64864  malware-automation   <- pgf self-design (C2/polymorphic 시그니처 탐지)
DESIGN CA  THR-ca2d7e92  credential-attack    <- pgf self-design (PassGAN/크래킹 시도 탐지)
DESIGN AE  THR-e4d97fa0  auto-exploitation    <- pgf self-design (LLM-exploit-gen 탐지)
```

## 사이클 산출물 (위협당)
```text
defenses/rules/{CODE}-001-{slug}.json     # 탐지 룰 (패턴/정책)
defenses/detectors/{slug}.py              # stdlib 탐지기 (verdict=데이터)
defenses/tests/{slug}_samples.jsonl       # 라벨 suite (malicious + 서술형 benign)
defenses/verify_{code}_001.py             # 증거 게이트 (exit 0 = pass)
defenses/{control}-mapping-{CODE}.md      # 거버넌스 매핑
.sisai/def-{threat_id}.json               # 방어 레코드 (verification.passed, implementations)
```

## 검증 게이트
```text
- 사이클별: recall==1.0 AND precision>=0.85 (verify_*.py exit 0)
- detector: 시계·난수·네트워크·AI import 0 (순수 stdlib)
- 무기화 산출 0 (working-exploit/c2/cracker/evasion 금지)
- record-defense: threat_marked != None → untriaged 감소 확인
- 최종: status untriaged==0 · validate PASS · unittest OK · build_report 2회 동일
```
