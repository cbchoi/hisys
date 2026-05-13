import json
from pathlib import Path

from hisys.hermes_deploy import deploy_hisys_to_hermes


def test_deploy_hisys_to_hermes_writes_wrapper_manifest_and_channel_snippet(tmp_path):
    source_root = tmp_path / "repo"
    source_root.mkdir()
    (source_root / "src").mkdir()
    target_root = tmp_path / ".hermes" / "tools" / "hisys"

    result = deploy_hisys_to_hermes(
        source_root=source_root,
        target_root=target_root,
        channel_id="1502110114704916501",
        channel_name="develop/Hisys",
        force=False,
    )

    assert result["status"] == "deployed"
    wrapper = target_root / "bin" / "hisys"
    manifest = target_root / "manifest.json"
    snippet = target_root / "hermes-channel-snippet.yaml"
    prompt = target_root / "channel-prompt.md"

    assert wrapper.exists()
    assert wrapper.stat().st_mode & 0o111
    wrapper_text = wrapper.read_text()
    assert str(source_root) not in wrapper_text
    assert "HISYS_RUNTIME_CONFIG" in wrapper_text
    assert "config/runtime.json" in wrapper_text
    assert "raw_source" in wrapper_text
    assert "releases/current/source" in wrapper_text
    assert "uv run --project" in wrapper_text
    assert "python -m hisys.cli.main" in wrapper_text

    runtime_config = json.loads((target_root / "config" / "runtime.json").read_text(encoding="utf-8"))
    assert runtime_config["schema_id"] == "hisys.hermes_tool_runtime_config"
    assert runtime_config["execution_mode"] == "installed_snapshot"
    assert runtime_config["source_root"] == str(target_root / "releases" / "current" / "source")
    assert runtime_config["source_root_policy"]["allow_live_source_checkout"] is False
    assert str(source_root) not in json.dumps(runtime_config)

    manifest_data = json.loads(manifest.read_text())
    assert manifest_data["tool_name"] == "hisys"
    assert manifest_data["upstream_source_root"] == str(source_root)
    assert manifest_data["source_root"] == str(target_root / "releases" / "current" / "source")
    assert manifest_data["deployment_mode"] == "immutable_snapshot"
    assert manifest_data["runtime_config"] == str(target_root / "config" / "runtime.json")
    assert manifest_data["wrapper"] == str(wrapper)
    assert manifest_data["channel_id"] == "1502110114704916501"
    assert manifest_data["safety_boundary"]["mutation_performed"] is False
    assert (target_root / "releases" / "current" / "source" / "src").exists()

    snippet_text = snippet.read_text()
    assert "1502110114704916501" in snippet_text
    assert "hisys-cli-tool" in snippet_text
    assert str(target_root) in snippet_text
    assert str(target_root / "releases" / "current" / "source") in prompt.read_text()
    assert str(source_root) not in prompt.read_text()


def test_deploy_hisys_to_hermes_refuses_existing_without_force(tmp_path):
    source_root = tmp_path / "repo"
    source_root.mkdir()
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    target_root.mkdir(parents=True)
    (target_root / "manifest.json").write_text("{}")

    result = deploy_hisys_to_hermes(source_root=source_root, target_root=target_root, force=False)

    assert result["status"] == "blocked"
    assert result["reason"] == "target_exists_use_force"


def test_deploy_hisys_to_hermes_force_replaces_existing_manifest(tmp_path):
    source_root = tmp_path / "repo"
    source_root.mkdir()
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    target_root.mkdir(parents=True)
    (target_root / "manifest.json").write_text('{"old": true}')

    result = deploy_hisys_to_hermes(source_root=source_root, target_root=target_root, force=True)

    assert result["status"] == "deployed"
    manifest_data = json.loads((target_root / "manifest.json").read_text())
    assert "old" not in manifest_data
    assert manifest_data["tool_name"] == "hisys"
