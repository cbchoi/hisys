# Claude Review — Hisys MCP Docker Service Implementation Plan

Read-only Claude Code advisory review captured on 2026-06-05. No repository edits, commits, external calls, or runtime mutations were authorized for the Claude review run.

## 결론

이 계획은 "Hermes 컨테이너 경량화"라는 목표에 대해 **방향성은 적절**하나, 실행 전에 결정해야 할 **transport·패키징·CLI adapter 안전성·DRLOO 브랜치 분리** 이슈가 남아 있어 약간의 보완이 필요합니다. `src/hisys/altas` 미존재(Open Question #3), MCP SDK transport 미확정(Open Question #1), 현재 작업 브랜치가 `drloo`인 상태에서 MCP 기능이 같은 브랜치로 섞일 위험이 가장 큰 보강 포인트입니다. 판정: **READY_WITH_REVISIONS**.

## 강점

- **Fail-closed 기본값**: `McpToolResultEnvelope`의 모든 live/mutation/publication 플래그가 false 기본, sampling default off (계획 라인 24–26, 199–213). 계획서 자체 `Boundary Record`도 명시.
- **얇은 표면적**: 1단계 노출 도구를 6개로 한정하고, browser/connector/DARS live/publication을 명시적 defer (라인 54–74). Hisys 거버넌스 경계와 일관.
- **기존 CLI seam을 그대로 활용**: 모든 명령 (`health-status`, `environment-status`, `list-run-artifacts`, `show-artifact`, `release-readiness`, `investigate-domain`)이 `src/hisys/cli/main.py` 내 실제 sub-parser와 일치 (예: `main.py:2752, 2760, 3310, 3318, 3425`).
- **TDD 강제**: RED → GREEN 명시, 각 Task에 실패 테스트 경로 적시 (Phase 1–4).
- **점진적 확장 경로**: gateway → service contracts → sidecar → 독립 MCP의 4단계 분리가 거버넌스 민감도(Judge 최후) 순서와 일치.
- **롤백 절차 명시**: 라인 648–663. Hermes config는 candidate-only로 표시.
- **Optional dependency 전략**: `[project.optional-dependencies].mcp` 추가로 base 설치 경량 유지 (라인 162–172, 현 `pyproject.toml` extras 패턴과 일치).

## 수정 권고 Top 10

1. **MCP SDK transport 확정**: 계획 Open Question #1은 코딩 전 폐쇄 필요. 현재 Python `mcp` SDK는 stdio + streamable-HTTP가 표준이며, "HTTP MCP"라는 표현이 모호. Task 4.1 시작 전 SDK 버전 핀(`mcp>=1.x,<2`)과 `streamable_http_server` vs `sse` 중 하나를 결정해 `server.py` 골격에 명시할 것.

2. **CLI adapter는 subprocess fork/exec 비용·startup import 비용을 매번 부담**: `hisys` 엔트리포인트(`pyproject.toml:39 hisys = "hisys.cli.main:main"`)는 무거운 import tree(pydantic, connectors, browser 등)를 매 호출 로드. Task 2.1 단계에서 (a) **per-tool in-process 호출 경로**를 1순위로 시도하고, subprocess는 격리가 필요한 경로(browser, live connector)로 한정하거나, (b) `python -m hisys.cli.main` 워밍업 데몬을 두는 옵션을 결정사항으로 추가.

3. **`environment-status` 인자 불일치**: 계획은 "environment_status"를 환경/머신 상태 도구로 매핑하지만 실제 CLI는 `--instance`가 없고 `--config`(기본 `DEFAULT_ENVIRONMENT_CONFIG`)만 받음(`main.py:2661–2663`). MCP 도구 시그니처에 `instance_root` 강제하면 사용 불가. 계획에 정확한 인자 mapping을 명시할 것.

4. **`investigate_domain`의 임시 request 파일 정책 부재**: Task 3.4가 "temp request file under the instance runtime"을 허용. 어떤 디렉터리 prefix(예: `${HISYS_INSTANCE_ROOT}/mcp/requests/<request_id>.json`)에 쓰는지, hashing/sanitize 규칙, 호출 종료 후 retention 정책을 contracts.py/policy로 못박지 않으면 path-injection·secret-leak 면이 생김. 또한 `--infer-domain-intent`(`main.py:3432`) 플래그 노출 여부도 명시.

5. **show-artifact 안전 ref 화이트리스트는 contracts 레벨에서 강제**: Task 3.3은 ".json/.md만, 절대경로/`..` 금지"를 도구 단에서 검증하라고 하지만, CLI도 동일 검증을 한다고 가정하면 이중방어 누락 시 회귀 위험. 정규식·resolve() 후 `instance_root` prefix 확인까지 명시.

6. **Approval ref 검증 계약 미정의**: `McpRequestEnvelope.approval_ref`가 옵셔널이지만 "유효한 approval인지" 판단 로직과 저장소(`docs/contracts/...` 또는 evidence store) 위치, TTL, 서명 정책이 비어 있음. 초기에는 "fail-closed: 어떤 approval_ref도 mutation/publication을 활성화하지 못함"이라고 단언하고, 이후 별도 Task로 분리.

7. **artifact_refs 캐리지 표준 부재**: 도구 결과의 `artifact_refs`가 "safe relative ref"인지, `instance://date/request_id/...` 같은 URI scheme을 쓰는지 미정. Hermes 측이 fetch할 방법(예: `show_artifact` 재호출)을 contracts.py 주석으로 못박을 것.

8. **Dockerfile 라인 가이드 보강**: Task 5.1은 base image와 entrypoint만 적시. **non-root user, `HISYS_INSTANCE_ROOT=/runtime` 기본 ENV, `pip install -e ".[mcp]"` (또는 빌드된 wheel) 채택, `/runtime` 볼륨 선언, `EXPOSE 8765`, healthcheck (`python -m hisys.mcp.server --health` 또는 `curl`-less in-process check), playwright/browser deps 미포함 명시**를 acceptance에 추가.

9. **Compose 마운트 경로 모호성**: `docker/compose.hisys-mcp-smoke.yaml`의 `./tmp/hisys-runtime:/runtime`은 compose 파일 위치 기준으로 `docker/tmp/...`에 만들어짐. `context: ..` 와 일관되게 `../tmp/hisys-runtime` 또는 `${PWD}/tmp/hisys-runtime`로 통일하고 `tmp/` 디렉터리 prebake/gitignore 결정사항을 명시할 것.

10. **Phase 6의 "altas_status 등 placeholder 도구"는 실수 노출 위험**: `src/hisys/altas` 패키지가 부재(글로브 확인)인 상태에서 도구 카탈로그에 이름만 등록하면 Hermes 측이 의도 외 호출. 계획대로 "blocked/error" 반환이지만, **초기 ToolList에서 노출 자체를 차단**하는 feature flag (`HISYS_MCP_EXPOSE_FUTURE_TOOLS=false` default)를 contracts.py에 추가할 것.

## 구현 전 필수 결정사항

- MCP SDK 버전 및 transport (stdio + streamable-HTTP) 동시 지원 여부, 의존성 핀.
- CLI 호출 방식: in-process 함수 호출 vs subprocess. 초기 슬라이스는 in-process 권고.
- `HISYS_INSTANCE_ROOT` 기본값(/runtime)과 Docker 볼륨 권한(root vs non-root) 정책.
- `artifact_refs` URI scheme(예: `runtime://<date>/<ref>`)과 직렬화 규칙.
- approval_ref 무시 정책(초기에는 무조건 무시·로그)을 contracts에 명시할 것인지.
- DRLOO 브랜치에서 분리할 새 feature 브랜치명(예: `feature/hisys-mcp-gateway`)과 PR 순서.
- `pyproject.toml`의 `mcp` 추가가 `[tool.hisys.traceability]` baseline에 변경 영향을 주는지 확인 (`pyproject.toml:51–57`).

## 가장 작은 첫 구현 slice

**Slice S0 (스코프)**: Task 1.1 + 1.2 + 1.3 + 3.1 의 `hisys_health_status`만, transport·Docker 없이.

- 파일: `src/hisys/mcp/__init__.py`, `src/hisys/mcp/contracts.py`, `src/hisys/mcp/config.py`, `src/hisys/mcp/tools.py` (health 한 개), `tests/unit/test_mcp_contracts.py`, `tests/unit/test_mcp_tools.py`.
- 호출 방식: **in-process** — `tools.py`에서 `_cmd_health_status`를 직접 import 또는 `health-status` 핸들러 본문 재사용. subprocess는 다음 슬라이스로.
- 변경 제외: `server.py`, Dockerfile, compose, Phase 6 placeholders.

**RED**: `pytest tests/unit/test_mcp_contracts.py tests/unit/test_mcp_tools.py -q` → 미존재로 실패.

**GREEN 기준**:
- 기본 envelope의 4개 안전 플래그 false.
- `hisys_health_status(instance_root=tmp_path, date="20260605")` 가 `status in {"ok","needs_more_evidence"}` 반환, `artifact_refs`에 `hisys-health-status.json`/`.md`가 포함.
- `external_call_made=false`, `mutation_performed=false`, `publication_or_live_action_approved=false`.

이 슬라이스 통과 후에야 cli_adapter(subprocess) → server transport → Docker 순으로 진입.

## 테스트/검증 제안

- **단위**:
  - `test_mcp_contracts.py::test_default_envelope_is_fail_closed`
  - `test_mcp_contracts.py::test_safety_flags_default_false`
  - `test_mcp_tools.py::test_health_status_returns_artifact_refs` (tmp 인스턴스)
  - `test_mcp_tools.py::test_show_artifact_rejects_absolute_path_and_dotdot`
  - `test_mcp_cli_adapter.py::test_secret_redaction` (`Authorization: Bearer xxx` → 마스킹)
  - `test_mcp_tools.py::test_investigate_domain_rejects_live_request_fields`
- **통합**: `test_mcp_server_smoke.py`는 stdio transport로 in-process 클라이언트 호출. HTTP smoke는 Docker 단계로 분리.
- **회귀**: Phase 7.2의 명령을 그대로 사용 (`tests/unit/test_health_status.py` 등).
- **Docker smoke**: `docker build -f Dockerfile.hisys-mcp -t hisys-mcp:local .` → compose up → 호스트에서 `python -m mcp.client.stdio` 또는 streamable-HTTP 클라이언트로 `tools/list`, `tools/call health_status` 호출. 기대: `external_call_made=false`.
- **거버넌스 게이트**: `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, `git diff --check`는 Phase 7.3 그대로.

## DRLOO 분리 권고

현재 브랜치가 `drloo`(작업 트리에 untracked `.hermes/plans/2026-06-05_205209-hisys-mcp-docker-service-plan.md` 존재)이고, `docs/plans/development-parallel-rloo-plan.md`는 DRLOO를 "shared_ledger_writer: integration-judge-only", "remote_push_authorized: false"로 lock하고 있음. 다음 권고를 적용해 DRLOO와 Hisys-MCP 구현을 격리하라.

1. **브랜치 분리**: `feature/hisys-mcp-gateway`(또는 `feat/mcp-sidecar`) 브랜치를 `main` 기준으로 새로 따고, MCP 구현 작업은 거기서만 진행. 현재 `drloo` 브랜치는 DRLOO 스캐폴드(`docs/rloo/parallel-lanes/drloo/...`)에 한정.
2. **DRLOO가 Hisys-MCP를 fixture로 소비**: DRLOO 측은 `verification_evidence.jsonl`/`gates.jsonl`에 Hisys-MCP 컨테이너를 "외부 도구 fixture"로 기록만 하고, MCP 코드/이미지를 직접 빌드/수정하지 않음. Compose 파일은 DRLOO lane에서 read-only로 참조.
3. **계획 파일 이동 위치 결정**: `.hermes/plans/...`(planning artifact)는 그대로 두고, Task 0.1의 `docs/plans/hisys-mcp-docker-service-implementation-tasks.md` 사본은 **MCP 브랜치에서만** 추가. DRLOO 브랜치에서 commit 금지.
4. **DRLOO ledger에는 Hisys-MCP 작업을 "external claim"으로 기록**: `development_claims.jsonl`에 `kind=external-dependency`, `subject=hisys-mcp-gateway`, `lane=feature/hisys-mcp-gateway`로 등록하여 단일-writer 통합 판단(Judge)이 lane 간 충돌을 인지 가능하게.
5. **integration-judge가 두 branch를 머지하는 정책**: Hisys-MCP가 `main`에 머지된 뒤에만 DRLOO 검증 게이트가 그것을 fixture로 사용할 수 있도록 순서 lock. Hermes config 변경(`mcp_servers.hisys`)은 운영자 승인 후에만, DRLOO 외부에서.

## 최종 판정

**READY_WITH_REVISIONS** — 위 "수정 권고 Top 10"의 최소 1·2·4·8·9·10번을 계획서 본문에 반영(혹은 명시적 Open Question으로 격상)하고, "구현 전 필수 결정사항"이 결정 기록으로 남은 뒤 Slice S0부터 진입할 것을 권고합니다.
