from __future__ import annotations

import pytest

from agentctx.core.resolver import ContextResolutionError, resolve_context
from agentctx.core.sanitizer import UnsafeContextError


def test_target_precedence_uses_cli_then_env_then_session_then_project_default(
    sample_context: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = sample_context["workspace"]
    agent_home = sample_context["agent_home"]

    cli_context = resolve_context(workspace, agent_home, cli_target="nas-test")
    assert cli_context.target.id == "nas-test"

    monkeypatch.setenv("AGENTCTX_TARGET", "cloud-prod")
    env_context = resolve_context(workspace, agent_home)
    assert env_context.target.id == "cloud-prod"

    monkeypatch.delenv("AGENTCTX_TARGET")
    session_context = resolve_context(workspace, agent_home)
    assert session_context.target.id == "local-dev"

    (workspace / ".agent" / "local.current.yaml").unlink()
    default_context = resolve_context(workspace, agent_home)
    assert default_context.target.id == "nas-test"


def test_resolved_context_uses_allowlisted_connection_and_remote_fields(sample_context: dict) -> None:
    context = resolve_context(
        sample_context["workspace"],
        sample_context["agent_home"],
        cli_target="nas-test",
    )

    assert context.project.id == "sample-app"
    assert context.project.name == "示例项目"
    assert context.connection.ssh_alias == "example-nas"
    assert context.connection.app_url == "http://192.0.2.10:8080"
    assert context.remote.app_dir == "/vol1/@team/示例团队/示例用户/sample-app"
    assert context.containers.postgres == "sample-postgres"
    assert context.secrets.configured is True
    assert context.secrets.readable_by_agent is False


def test_resolver_discovers_project_from_nested_workspace_path(sample_context: dict) -> None:
    nested = sample_context["workspace"] / "src" / "feature"
    nested.mkdir(parents=True)

    context = resolve_context(nested, sample_context["agent_home"], cli_target="nas-test")

    assert context.project.id == "sample-app"
    assert context.project.workspace == str(sample_context["workspace"])
    assert context.target.id == "nas-test"


def test_show_context_fails_before_returning_secret_like_values(sample_context: dict) -> None:
    device_path = sample_context["agent_home"] / "devices" / "example-nas.yaml"
    text = device_path.read_text(encoding="utf-8")
    device_path.write_text(text.replace("http://192.0.2.10:8080", "sk-test-leaked"), encoding="utf-8")

    with pytest.raises(UnsafeContextError):
        resolve_context(sample_context["workspace"], sample_context["agent_home"], cli_target="nas-test")


def test_missing_binding_reports_clear_error(sample_context: dict) -> None:
    (sample_context["agent_home"] / "bindings" / "sample-app.nas-test.yaml").unlink()

    with pytest.raises(ContextResolutionError, match="binding"):
        resolve_context(sample_context["workspace"], sample_context["agent_home"], cli_target="nas-test")
