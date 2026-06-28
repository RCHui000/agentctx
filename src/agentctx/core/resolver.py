from __future__ import annotations

import os
from pathlib import Path

from agentctx.core.loader import (
    ConfigLoadError,
    get_agent_home,
    load_binding,
    load_device,
    load_project,
    load_session,
)
from agentctx.core.models import (
    ConnectionBrief,
    ContainersBrief,
    ContextBrief,
    ProjectBrief,
    RemoteBrief,
    SafetyBrief,
    SecretsBrief,
    TargetBrief,
)
from agentctx.core.sanitizer import assert_safe_output, bool_value, first_text


class ContextResolutionError(RuntimeError):
    pass


def resolve_target(cli_target: str | None, env_target: str | None, session_target: str | None, default_target: str | None) -> str:
    for candidate in (cli_target, env_target, session_target, default_target):
        if candidate:
            return candidate
    raise ContextResolutionError("No target provided and project has no default_target")


def resolve_context(
    workspace: Path | str | None = None,
    agent_home: Path | str | None = None,
    *,
    cli_target: str | None = None,
    project_id: str | None = None,
) -> ContextBrief:
    root, project = load_project(workspace)
    if project_id is not None and project_id != project.project_id:
        raise ContextResolutionError(f"Project id {project.project_id!r} does not match requested {project_id!r}")

    home = get_agent_home(agent_home)
    session = load_session(root)
    target_id = resolve_target(
        cli_target,
        os.environ.get("AGENTCTX_TARGET"),
        session.current_target if session else None,
        project.default_target,
    )
    target = project.targets.get(target_id)
    if target is None:
        raise ContextResolutionError(f"Unknown target: {target_id}")

    brief = ContextBrief(
        project=ProjectBrief(
            id=project.project_id,
            name=project.name,
            workspace=str(root),
            docs=project.docs,
        ),
        target=TargetBrief(
            id=target_id,
            kind=target.kind,
            risk=target.risk,
            require_confirm=target.require_confirm,
        ),
        docs=project.docs,
        safety=SafetyBrief(prod_requires_confirmation=target.require_confirm),
    )

    if target.binding:
        try:
            binding = load_binding(home, target.binding)
        except ConfigLoadError as exc:
            raise ContextResolutionError(f"Missing binding {target.binding}: {exc}") from exc
        if binding.project_id != project.project_id:
            raise ContextResolutionError(f"Binding {binding.binding_id} belongs to project {binding.project_id}")
        if binding.target_id != target_id:
            raise ContextResolutionError(f"Binding {binding.binding_id} belongs to target {binding.target_id}")

        device = None
        if binding.device_id:
            try:
                device = load_device(home, binding.device_id)
            except ConfigLoadError as exc:
                raise ContextResolutionError(f"Missing device {binding.device_id}: {exc}") from exc

        brief.remote = RemoteBrief(
            app_dir=binding.remote.get("app_dir"),
            supabase_dir=binding.remote.get("supabase_dir"),
        )
        brief.containers = ContainersBrief(
            app=binding.containers.get("app"),
            postgres=binding.containers.get("postgres"),
            reverse_proxy=binding.containers.get("reverse_proxy"),
        )
        brief.safety = SafetyBrief(
            sudo_requires_confirmation=bool_value(binding.deploy.get("requires_sudo")),
            remote_exec_enabled=bool_value(binding.deploy.get("remote_exec_enabled")),
            prod_requires_confirmation=target.require_confirm,
            forbidden=binding.forbidden_commands,
        )

        if device:
            brief.connection = ConnectionBrief(
                device=device.device_id,
                host=first_text(device.ssh, ("host", "hostname")) or first_text(device.network, ("host",)),
                ssh_alias=first_text(device.ssh, ("alias",)),
                app_url=first_text(device.network, ("app_url",)),
                app_direct_url=first_text(device.network, ("app_direct_url",)),
            )
            brief.secrets = SecretsBrief(
                configured=bool_value(device.secrets.get("configured")),
                readable_by_agent=bool_value(device.secrets.get("readable_by_agent")),
            )
            if bool_value(device.policy.get("require_confirm_for_sudo")):
                brief.safety.sudo_requires_confirmation = True

    assert_safe_output(brief.model_dump(mode="json", exclude_none=True))
    return brief
