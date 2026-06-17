# ARCHITECTURE — SISAI 3가닥 ↔ 구현 매핑

> 설계 정본: `.pgf/DESIGN-SISAI.md`. 운영 지시문: `docs/INSTRUCTIONS-sisai-cycle.md`.

## 1. 명제

하나의 결정론 백본(`core/`)이 세 가닥을 단일 출처로 묶고, `next_action`이 매 턴 어느 가닥을
돌릴지 정하며, **검증된 방어가 코퍼스로 환류**되어 수렴 없이 복리로 도는 나선을 이룬다.
채널 자체가 1급 자산으로 발굴·기록·재사용된다.

## 2. 가닥 ↔ 모듈

| 가닥 | 역할 | AI 메타층(skills) | 결정론 백본(core/) |
|---|---|---|---|
| **A. ThreatIntel** | 채널 스캔→위협 수집·분류 | 실제 스캔·추출 | `channels`(스캔 후보), `ledger`(중복차단), `triage`(우선순위), `diversity`(사각지대) |
| **B. DefenseSynth** | 해결책 외부탐색→없으면 자체설계 | 외부 검색, **pgf full-cycle 설계** | `loop.plan_defense`(외부우선 결정), `provenance`(계보) |
| **C. DetectOps** | 탐지 규칙/리포트 운영→성과 환류 | 규칙 적용·평가 | `provenance.defense_to_corpus_entry`(검증후 환류), `ledger`(기록) |
| **채널 자기확장** | 새 정보원 발굴·등록 | 새 소스 발견 | `channels.register_channel`(기록·dedup), `should_discover_channels` |

## 3. next_action 우선순위 (결정론)

```
RECORD_DEFENSE   (검증된 방어 → ledger+코퍼스 환류; 최우선, 고리 닫기)
→ DISCOVER_CHANNELS (활성 채널/커버리지 부족 → 정보원 확장)
→ REFRESH_COVERAGE  (공격표면 쏠림 → 미커버 카테고리로 조향)
→ RUN_THREAT_INTEL  (미처리 위협 0 & 채널 있음 → 신선 위협 수집)
→ SOLVE_OR_DESIGN   (최우선 위협 처리: 외부우선 → 없으면 pgf 설계)
```

## 4. 자재 흐름 (한 줄)

```
채널 발굴 → 채널 스캔 → 위협 수집(triage) → [외부 방어 탐색 ─ 있으면 채택]
                                            └ 없으면 pgf 자체설계 → 검증 → ledger 기록
                                                                       └ 코퍼스 환류(염기쌍) ┐
   ▲ 매 턴 사각지대 측정(diversity)·재사용 차단(ledger)·우선순위(triage) ────────────────────┘
```

## 5. 결정론 경계 (지배 제약)

```
core/ (sisai.py CLI 엣지 제외)  → 순수 결정론 (stdlib; now 주입). 수집 텍스트가 제어흐름 불변.
AI 메타층 (skills)              → 채널 발견·위협 이해·방어 설계 (비결정론 허용, 출력은 schema 검증)
defensive-only                 → 탐지/방지/리포트만. 무기화 산출 범위 밖.
wall-clock                     → sisai.py CLI 엣지에서만 (--now 주입 우선)
```

## 6. 확장점 — N가닥

불변항은 가닥 수가 아니라 백본이다. 새 가닥(예: ComplianceMap, RedTeamSim)을 더하려면
어댑터(`engines/`)와 `next_action` 분기만 추가하면 된다. 백본·결정론 경계는 불변.

## 7. HELIX와의 관계

설계 *패턴*(explore⊕exploit+백본 나선, ledger/diversity/provenance/atomic-io/schema-walker)을
계승했으나 **코드 의존 0**. SISAI는 보안 도메인 고유 개념(채널 자기확장·triage·외부우선
자체설계·self-defense)으로 독립 구현되어 SISAI 폴더만으로 구동된다.
