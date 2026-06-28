from __future__ import annotations

import json

import yaml
from typer.testing import CliRunner

from agentctx.cli import app


runner = CliRunner()


def test_show_text_outputs_context_without_secret_references(sample_context: dict) -> None:
    result = runner.invoke(app, ["show", "--target", "nas-test"])

    assert result.exit_code == 0
    assert "Agent Context Brief" in result.stdout
    assert "示例项目" in result.stdout
    assert "example-nas" in result.stdout
    assert "/vol1/@team/示例团队/示例用户/sample-app" in result.stdout
    assert ".env" not in result.stdout
    assert ".pem" not in result.stdout
    assert "agentctx-secret:example-nas/app-env" not in result.stdout


def test_show_json_outputs_reusable_brief(sample_context: dict) -> None:
    result = runner.invoke(app, ["show", "--target", "nas-test", "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project"]["id"] == "sample-app"
    assert data["target"]["id"] == "nas-test"
    assert data["connection"]["ssh_alias"] == "example-nas"
    assert data["remote"]["app_dir"] == "/vol1/@team/示例团队/示例用户/sample-app"
    assert data["secrets"]["readable_by_agent"] is False


def test_show_audit_log_keeps_only_metadata(sample_context: dict) -> None:
    result = runner.invoke(app, ["show", "--target", "nas-test"])

    assert result.exit_code == 0
    audit_path = sample_context["agent_home"] / "audit" / "agentctx.log.jsonl"
    audit_text = audit_path.read_text(encoding="utf-8")
    event = json.loads(audit_text.splitlines()[-1])
    assert event["cmd"] == "show"
    assert event["project"] == "sample-app"
    assert event["target"] == "nas-test"
    assert event["result"] == "ok"
    assert "app_dir" not in audit_text
    assert "example-nas" not in audit_text
    assert "示例团队" not in audit_text
    assert "agentctx-secret:example-nas/app-env" not in audit_text


def test_list_outputs_project_targets(sample_context: dict) -> None:
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["local-dev", "nas-test", "cloud-prod"]


def test_use_writes_only_workspace_session(sample_context: dict) -> None:
    result = runner.invoke(app, ["use", "nas-test"])

    assert result.exit_code == 0
    session_path = sample_context["workspace"] / ".agent" / "local.current.yaml"
    session = yaml.safe_load(session_path.read_text(encoding="utf-8"))
    assert session["schema"] == "agentctx.session/v1"
    assert session["current_target"] == "nas-test"
    assert not (sample_context["agent_home"] / "local.current.yaml").exists()


def test_show_rejects_wrong_project_id(sample_context: dict) -> None:
    result = runner.invoke(app, ["show", "--project", "wrong", "--target", "nas-test"])

    assert result.exit_code != 0
    assert "does not match" in result.stdout


def test_server_list_discovers_global_devices_without_project_folder(sample_context: dict, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["server", "list"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["example-nas"]


def test_server_show_outputs_safe_connection_brief_without_project_folder(sample_context: dict, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["server", "show", "example-nas", "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["device"]["id"] == "example-nas"
    assert data["connection"]["ssh_alias"] == "example-nas"
    assert data["connection"]["host"] is None
    assert data["secrets"]["readable_by_agent"] is False
    assert "agentctx-secret:example-nas/app-env" not in result.stdout


def test_server_show_blocks_secret_like_network_values(sample_context: dict, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    device_path = sample_context["agent_home"] / "devices" / "example-nas.yaml"
    text = device_path.read_text(encoding="utf-8")
    device_path.write_text(text.replace("http://192.0.2.10:8080", "sk-leaked-value"), encoding="utf-8")

    result = runner.invoke(app, ["server", "show", "example-nas"])

    assert result.exit_code != 0
    assert "Refusing to render" in result.stdout
