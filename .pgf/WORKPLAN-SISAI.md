# WORKPLAN-SISAI @v:0.1

> 설계: `.pgf/DESIGN-SISAI.md`. 목표: 자기완결(HELIX 독립) self-improvement security AI.
> 계승: HELIX 백본 패턴(결정론 stdlib). 고유: 채널 자기확장 + 외부우선-자체설계 + triage.

## POLICY
```yaml
preserve_determinism: true     # core stdlib; now만 주입
self_contained: true            # SISAI 폴더만으로 구동; HELIX import 0
defensive_only: true            # 무기화 산출 차단
verify_each: true
```

## 배치 (의존 순서)
```text
B0 Fingerprint        (designing)  core/sisai_fingerprint.py — 정규화·지문
B1 Io+Schema          (designing) @dep:B0  atomic write + JSON-Schema-subset checker
B2 Channels           (designing) @dep:B0,B1  ★ 채널 레지스트리(발굴·기록·재사용)
B3 Ledger             (designing) @dep:B0  위협/방어/채널 재사용 게이트
B4 Diversity+Triage   (designing) @dep:B0  커버리지(사각지대) + severity×recency
B5 Provenance         (designing) @dep:B0  위협→방어 계보 + 검증방어→코퍼스 환류
B6 Loop               (designing) @dep:B4  next_action(3가닥) + SolveOrDesign 정책
B7 Engines            (designing) @dep:B3,B5  threat/defense/channel 어댑터
B8 Driver             (designing) @dep:B2,B6,B7  sisai.py status/discover/record/loop-status
B9 Schemas+Seed       (designing) @dep:B1  계약 5종 + 요약.md → taxonomy/defense/channel 시드
B10 Validate          (designing) @dep:all  구조+계약 검증기
B11 Docs              (designing)  README/RUNBOOK/ARCHITECTURE/SELF-DEFENSE/INSTRUCTIONS
B12 Tests             (designing) @dep:all  결정론 unittest (채널/ledger/triage/loop/io/schema/provenance/self-defense)
B13 Verify            (needs-verify) @dep:all  unittest+validate+status+결정론 2회
```

## 검증 게이트
```text
- unittest discover OK (결정론 2회 동일) · validate PASS · status 정상
- core: 시계·난수·네트워크·AI·HELIX import 0 · 자기완결(폴더만으로 구동)
- 채널 idempotent · 외부우선 · 방어 환류는 검증 후 · 인젝션 방어 테스트 통과
```
