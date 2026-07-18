# tmux 실측 스모크 테스트 기록 (Task 8)

- 일시: 2026-07-08, 로컬 Mac, tmux 세션 `sp-test`, 전용 프로필 `sptest` (gpt-5.5 / openai-codex 프록시)
- 설치: `~/.hermes/profiles/sptest/plugins/superpowers/` (rsync 복사, `hermes plugins enable superpowers`)

## 체크리스트 결과

| #   | 항목                                                | 결과                                                                                                        |
| --- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | `/plugins`에 superpowers 표시                       | ✅ `✓ superpowers v0.3.0 (2 tools, 3 hooks, 3 commands)`                                                    |
| 2   | `/sp-status` → phase: idle                          | ✅ 전체 phase 목록 포함 출력                                                                                |
| 3   | 첫 턴 부트스트랩 주입                               | ✅ 에이전트가 주입 지시에 따라 `skill_view("superpowers:using-superpowers")` 자발 호출 + 워크플로 규칙 인지 |
| 4   | `/sp-phase brainstorming` 전이                      | ✅ 전이 + 리마인더 출력                                                                                     |
| 5   | 게이트 강제 관찰 (idle 상태 구현 요청)              | ✅ "I can't create greet.py yet because your gate says: HARD GATE..." — 거부 + 설계 제안 + 승인 요청        |
| 6   | `skill_view("superpowers:test-driven-development")` | ✅ 로드, 첫 헤딩 "Test-Driven Development (TDD)" 반환                                                       |

## 실측 중 발견·수정한 결함 (상세: .superpowers/sdd/task-8-notes.md)

1. **패키지 로딩 임포트 실패** — flat import가 패키지 컨텍스트에서 실패 (`No module named 'commands'`) → 이중 임포트 패턴 (bb15b89)
2. **ctx API 시그니처 불일치** — register_tool(name, toolset, schema, handler), register_skill(name, Path) → 정합 수정 + _safe 로깅 (44f8939)

## 미관찰 항목

- post_tool_call 쓰기 경고 승격: 라이브에서는 게이트 준수로 쓰기 자체가 발생하지 않아 미관찰 (유닛 테스트로 커버)
- post_tool_call의 세션 키가 실제로 task_id로 오는지 실환경 미확인 (경고 승격이 세션 단위로 정확히 매칭되는지) — codex 리뷰 관찰 대상
