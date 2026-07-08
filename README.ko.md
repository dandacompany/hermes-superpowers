# hermes-superpowers (한국어)

[obra/superpowers](https://github.com/obra/superpowers)를
[Hermes Agent](https://github.com/NousResearch/hermes-agent)용으로 완전
이식한 플러그인입니다. 브레인스토밍·플랜 작성·서브에이전트 기반 개발·TDD·
체계적 디버깅·코드 리뷰 등 14종의 프로세스 스킬, 에이전트가 프로세스를
벗어나지 않도록 매 턴 리마인드를 주입하는 훅 레이어, 그리고 Hermes의
`delegate_task` 서브에이전트 모델에 맞춘 SDD(스펙 주도 개발) 워크플로를
제공합니다.

정본(upstream)은 Claude Code를 대상으로 하지만, 이 플러그인은 같은 스킬과
워크플로 규율을 Hermes 플러그인 형태로 재구현합니다: `plugin.yaml` +
`register(ctx)` 와이어링, 작은 8단계 상태기계, 슬래시 커맨드 3종, 그리고
에이전트가 직접 호출해 워크플로를 진행시킬 수 있는 툴 1종.

## 설치

Hermes 플러그인은 `~/.hermes/plugins/` 아래에 `plugin.yaml` 매니페스트와
`register(ctx)`를 노출하는 `__init__.py`를 가진 디렉토리입니다 — 이
리포지토리 루트가 이미 그 구조입니다.

### 옵션 A — clone + symlink (개발 시 권장)

```bash
git clone https://github.com/dandacompany/hermes-superpowers.git ~/src/hermes-superpowers
mkdir -p ~/.hermes/plugins
ln -s ~/src/hermes-superpowers ~/.hermes/plugins/superpowers
```

`ln -s` 대신 `cp -r`로 그냥 복사해도 동일하게 동작합니다. 심볼릭 링크를
쓰면 원본 체크아웃에서 `git pull`만 해도 플러그인이 바로 갱신된다는 차이만
있습니다.

### 옵션 B — `hermes plugins install`

리포지토리가 GitHub에 있다면 Hermes가 직접 `~/.hermes/plugins/`로 클론해
줍니다:

```bash
hermes plugins install dandacompany/hermes-superpowers
```

`owner/repo` 축약형이나 전체 git URL을 모두 받습니다. 설치 후
`Enable 'superpowers' now? [y/N]`라고 묻는데 `y`를 입력하거나, 스크립트
설치 시 프롬프트를 건너뛰려면 `--enable` / `--no-enable`을 사용하세요.
로컬 파일 경로는 받지 않으므로, 로컬 체크아웃이라면 옵션 A를 쓰세요.

### 확인

```bash
hermes plugins list
```

`superpowers`가 `Source: git`(옵션 B) 또는 로컬 디렉토리(옵션 A), 버전
`0.1.0`, 상태 `not enabled`로 표시되어야 합니다 — 플러그인은 기본적으로
옵트인입니다. 활성화:

```bash
hermes plugins enable superpowers
```

이때 `Allow this plugin to replace built-in tools (e.g. shell_exec,
write_file)? [y/N]`라고 묻습니다 — **no**로 답하세요. 이 플러그인은 훅과
툴 1종, 커맨드 3종만 등록할 뿐 어떤 내장 툴도 오버라이드하지 않습니다.
세션을 재시작하거나(게이트웨이라면 `hermes gateway restart`) 새 세션을
시작하면 플러그인이 적용됩니다.

플러그인이 목록에 안 보이거나 보이는데 로드가 안 되면, 상세 로그를 켜서
확인하세요:

```bash
HERMES_PLUGINS_DEBUG=1 hermes plugins list
```

또는 저장된 로그를 확인:

```bash
hermes logs --level WARNING | grep -i plugin
```

## 슬래시 커맨드

| 커맨드              | 동작                                                                                                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/superpowers`      | 워크플로 진입점을 로드합니다 — 에이전트에게 `superpowers:using-superpowers`를 읽고 프로세스(창작 작업 전 브레인스토밍, 코드 작성 전 플랜, 빌드 시 서브에이전트 기반 개발)를 따르라고 지시합니다. |
| `/sp-status`        | 현재 워크플로 단계와 전체 단계 목록을 출력합니다.                                                                                                                                                |
| `/sp-phase <phase>` | 워크플로 단계를 명시적으로 설정합니다(아래 8단계 중 하나). 알 수 없는 단계명은 거부합니다.                                                                                                       |

## 훅 동작 방식

훅 3종이 등록됩니다(`pre_llm_call`, `on_session_start`,
`post_tool_call`). 어느 것도 툴 호출을 차단하지 않습니다 — 강제가 아니라
리마인드 기반 설계입니다:

- **첫 턴 부트스트랩** (`pre_llm_call`, `is_first_turn=True`): `<superpowers-bootstrap>`
  태그로 감싼 `using-superpowers` 스킬 전문(파일을 읽지 못하면 대체 요약)을
  주입합니다. 정본의 `SessionStart` 훅과 같은 역할입니다.
- **매 턴 게이트 리마인더** (`pre_llm_call`, 이후 모든 턴): 현재 단계와
  무엇이 막고 있는지("디자인 승인 전에는 구현 금지" 등)를 한 줄로
  `<superpowers-gate>` 태그에 담아 주입합니다.
- **쓰기 툴 경고 승격** (`post_tool_call` + 다음 `pre_llm_call`): 워크플로가
  구현 이전 단계(`idle` ~ `plan-approved`)인데 파일을 쓰는 툴(`write_file`,
  `patch`)이 실행되면, 다음 턴의 게이트 리마인더가 `WARNING`으로 격상되어 에이전트에게
  멈추고 디자인/플랜 게이트로 돌아가라고 알립니다.
- **세션 리셋** (`on_session_start`): 단계를 `idle`로 되돌리고 대기 중인
  경고를 지워서, 새 세션은 항상 깨끗한 상태로 시작합니다.

여기서 어떤 것도 툴 호출을 강제로 막지 않습니다 — 이유는 아래 "정본과의
차이"를 참고하세요.

## 워크플로 단계

`idle → brainstorming → design-approved → planning → plan-approved →
implementing → reviewing → done`

에이전트가 스스로 단계를 전이시킵니다. `/sp-phase <phase>` 또는
`superpowers_phase` 툴 호출(효과는 동일, 툴로도 호출 가능) 둘 중 하나로요.
**승인 단계**(`design-approved`, `plan-approved`)는 사람이 디자인이나
플랜을 명시적으로 승인한 뒤에만 설정하도록 의도되어 있습니다 — 훅과 스킬
텍스트가 이를 반복해서 상기시키지만, 에이전트가 이 규칙을 건너뛰는 것을
코드가 막지는 않습니다. 에이전트가 지키기로 되어 있는 문서화된 관례입니다.

## Hermes에서의 SDD(스펙 주도 개발)

`subagent-driven-development`와 `dispatching-parallel-agents`는 Claude
Code의 Task tool 대신 `delegate_task`를 쓰도록 이식되었습니다. 실무에서는:

- 구현은 **구현자 + 리뷰어 쌍**으로 진행됩니다: 플랜의 한 태스크를
  구현하는 `delegate_task`를 하나 디스패치하고, 그 다음 diff를 리뷰하는
  두 번째 `delegate_task`를 디스패치합니다. REJECT 판정이 나오면 수정
  구현자 디스패치가 트리거되며(최대 2라운드까지, 이후엔 오케스트레이터로
  에스컬레이션).
- `delegate_task`로 시작된 자식은 **부모 대화 이력이 전혀 없고**
  **`clarify`를 호출할 수 없습니다** — 자식의 질문은 반드시 오케스트레이팅
  에이전트가 중계해야 합니다.
- `delegate_task` 디스패치는 부모 턴이 중단되면 **durable하지 않으므로**,
  플랜은 **태스크마다 커밋**하며 실행됩니다: 완료된 태스크마다 커밋한 뒤
  다음으로 넘어가서, 재개 시 진행 중이던 서브에이전트 작업을 replay할
  필요가 없습니다.
- 독립적인 태스크 묶음은 `delegate_task(tasks=[...])`로 처리하며,
  `max_concurrent_children`(기본 3, `DELEGATION_MAX_CONCURRENT_CHILDREN`으로
  오버라이드 가능)로 상한을 둡니다 — 상한을 넘는 배치는 실패가 아니라
  큐에 대기합니다.

Claude Code → Hermes 전체 툴 매핑과 정본 재동기화 시 적용되는 기계적
치환 규칙은 `references/tool-mapping.md`를 참고하세요.

## 정본과의 차이

- **컴팩션 훅 없음.** Claude Code에는 컨텍스트 압축 후 프로세스 리마인더를
  재주입하는 `PostCompact` 훅이 있지만, Hermes에는 대응 개념이 없습니다.
  그래서 이 플러그인은 대신 **매 턴** `pre_llm_call`로 단계 리마인더를
  주입하고, 잘못된 쓰기가 발생하면 `WARNING`으로 격상시킵니다.
- **하드 차단 없음 — 설계 의도.** 여기 있는 모든 훅은 best-effort이며
  리마인드 전용입니다(각자 예외를 잡아 안전하게 실패). 워크플로 규율은
  플러그인이 툴 실행을 거부하는 것이 아니라, 에이전트가 주입된 리마인더를
  읽고 지키는 것에 달려 있습니다.
- **Skill tool 대신 `skill_view`.** Claude Code의 `Skill tool` /
  `superpowers:<name>` 호출은 Hermes에서 `skill_view("superpowers:<name>")`가
  됩니다. 14개 스킬 전부가 `tools_dev/sync_upstream.py`로 기계적으로
  재매핑되었고, 몇 군데는 `tools_dev/MANUAL_FIXUPS.md`에 기록된 손수
  작성한 문단이 추가되어 있습니다.
- **타 하네스 어댑테이션 파일 제거.** 정본에는 이 포트가 실행하지 않는
  하네스(Codex, Pi, Antigravity)용 레퍼런스 문서와 Claude Code 전용
  실습 예제(`CLAUDE_MD_TESTING.md`), 그리고 정본 개발 로그
  (`CREATION-LOG.md`)가 포함되어 있습니다. Hermes에는 해당 사항이 없으므로
  매핑하지 않고 그대로 삭제했습니다. 무엇을 지웠고 재동기화 시 어떻게
  다시 유지되는지는 `tools_dev/MANUAL_FIXUPS.md`를 참고하세요.

## 강의 수강생용 따라하기 절차

인프런 Hermes 강의 수강생이라면 아래 순서대로 직접 실행해 보며
훅 동작을 관찰하세요.

1. **설치** — 위 "설치" 섹션의 옵션 A 또는 B로 플러그인을 설치합니다.
2. **`/plugins` 로 확인** — Hermes CLI 세션 안에서 `/plugins`를 입력해
   `superpowers`가 목록에 뜨는지 확인합니다. (터미널에서는
   `hermes plugins list`로도 같은 것을 볼 수 있습니다.)
3. **활성화** — `hermes plugins enable superpowers` 실행 후 새 세션을
   시작합니다.
4. **`/sp-status` 로 초기 상태 확인** — 새 세션에서 `/sp-status`를
   입력하면 `idle` 단계와 8단계 전체 목록이 출력됩니다.
5. **간단한 기능 요청으로 게이트 관찰** — "이런 기능을 추가해줘" 같은
   요청을 던져 보고, 응답 상단/맥락에 `<superpowers-bootstrap>`(첫 턴) 또는
   `<superpowers-gate>`(이후 턴) 태그로 감싸인 리마인더가 실제로 주입되는지
   확인합니다. 에이전트가 브레인스토밍이나 플랜 작성 없이 바로 파일을
   쓰려고 하면, 다음 턴의 게이트 리마인더가 `WARNING`으로 바뀌는 것도
   관찰 포인트입니다.
6. **단계 전이 확인** — 에이전트가 (또는 여러분이 `/sp-phase design-approved`
   같은 명령으로) 단계를 전이시킨 뒤 `/sp-status`로 반영됐는지 다시
   확인합니다.

이 흐름 전체가 "훅은 차단하지 않고 리마인드만 한다"는 이 플러그인의
설계 철학을 직접 눈으로 확인하는 과정입니다.

## 어트리뷰션

[obra/superpowers](https://github.com/obra/superpowers) 6.1.1(Jesse
Vincent 작성, MIT 라이선스)을 기반으로 합니다. 여기 실린 14개 스킬
본문은 정본을 거의 그대로 미러링한 뒤 Hermes 툴 이름만 치환한
것입니다. 재동기화 절차는 `UPSTREAM.md`를 참고하세요.
