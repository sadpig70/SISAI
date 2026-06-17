# SISAI RUNBOOK — 폴더 하나로 전 기능 실행

> SISAI는 자기완결이다. `skills/`에 pg/pgf/pgxf, `core/`에 결정론 백본, `sisai.py`에 드라이버,
> `seed/`에 시드 코퍼스가 있다. 스킬은 AI-native(parser-free) — `SKILL.md`를 로드하면 AI 런타임이 수행한다.

## 0. 두 실행 경로

| 경로 | 무엇 | 어떻게 |
|---|---|---|
| **AI-native (주)** | 채널 발견·위협 이해·방어 설계 | AI 런타임이 `skills/{pg,pgf,pgxf}` + `docs/INSTRUCTIONS-sisai-cycle.md` 로드 후 수행 |
| **결정론 백본 (제어)** | 상태·우선순위·기록·환류 | `python sisai.py ...` (stdlib) |

## 1. 드라이버 명령

| 기능 | 명령 | 산출 |
|---|---|---|
| 한 턴 상태 | `python sisai.py status --now <date>` | 채널/위협/triage/방어계획/next_action |
| 방어 조달 전략 | `python sisai.py plan --now <date>` | ADOPT_EXTERNAL / DESIGN_DEFENSE |
| 채널 발굴·기록 | `python sisai.py discover-channel --channel ch.json --registry .sisai/channels.json` | dedup 등록 |
| 고리 닫기 | `python sisai.py record-defense --defense def.json --ledger .sisai/ledger.json --corpus .sisai/corpus.json` | ledger+코퍼스 환류 |
| 위협 적재 | `python sisai.py ingest-threats --threats new.json --ledger .sisai/ledger.json` | schema 검증·dedup 후 `.sisai/threats.json` (RUN_THREAT_INTEL 출력) |

## 2. 검증·테스트

```bash
python core/sisai_validate.py .                      # 구조 + 계약 스키마 + seed
python core/sisai_validate.py . --integrity --live   # 스킬 해시 무결성 + .sisai 런타임 상태
python core/sisai_validate.py . --write-integrity    # 스킬 변경 후 무결성 매니페스트 재생성
python defenses/verify_all.py                         # 10개 방어 suite 일괄 (per-suite + overall)
python -m unittest discover -s tests -q              # 결정론 테스트
python -m compileall core engines sisai.py defenses   # stdlib 컴파일
```

## 3. 자율 실행 (문서만 읽고 한 턴)
`docs/INSTRUCTIONS-sisai-cycle.md` — 상태 로드 → next_action → 가닥 수행(외부우선/자체설계) →
검증 → close-loop. 자기방어·결정론·무기화금지 불가침.

## 4. 입력 파일 형식 (예)

`ch.json` (발굴 채널):
```json
{"kind": "exploit_db", "url": "https://www.exploit-db.com/", "discovered_from": "CH-google-gtig"}
```

`def.json` (검증된 방어 — record-defense 입력):
```json
{"defense_id": "DEF-promptguard", "title": "Indirect prompt-injection filter",
 "kind": "designed", "controls": ["input-isolation", "tool-allowlist"],
 "covers_threat": "THR-...", "source_channels": ["CH-owasp-llm"],
 "verification": {"method": "redteam-suite", "passed": true},
 "implementations": [{"rule_id": "PI-001", "artifact_path": "rules/pi_001.yaml"}]}
```

## 5. 런타임 디렉토리 (생성물 — gitignore 권장)
`.sisai/` (channels.json·ledger.json·corpus.json) 는 실행 중 루트에 생성된다.
durable 시드는 `seed/`. 없으면 드라이버는 `seed/`로 폴백한다.

## 6. 전체 흐름 (한 줄)
```
채널발굴 → 스캔 → 위협수집(triage) → 외부방어탐색 ─있으면─ 채택
                                        └없으면─ pgf 자체설계 → 검증 → ledger+코퍼스 환류 ┐
   ▲ 매 턴 사각지대(diversity)·재사용(ledger)·우선순위(triage)·자기방어(SELF-DEFENSE) ─────┘
```
