from __future__ import annotations

from pathlib import Path

from agentctx.core.loader import get_agent_home, load_device
from agentctx.core.models import ConnectionBrief, DeviceBrief, SafetyBrief, SecretsBrief, ServerBrief
from agentctx.core.sanitizer import assert_safe_output, bool_value, first_text


def resolve_server(device_id: str, agent_home: Path | str | None = None) -> ServerBrief:
    home = get_agent_home(agent_home)
    device = load_device(home, device_id)
    brief = ServerBrief(
        device=DeviceBrief(id=device.device_id, kind=device.kind, display_name=device.display_name),
        connection=ConnectionBrief(
            device=device.device_id,
            host=first_text(device.ssh, ("host", "hostname")) or first_text(device.network, ("host",)),
            ssh_alias=first_text(device.ssh, ("alias",)),
            app_url=first_text(device.network, ("app_url",)),
            app_direct_url=first_text(device.network, ("app_direct_url",)),
        ),
        secrets=SecretsBrief(
            configured=bool_value(device.secrets.get("configured")),
            readable_by_agent=bool_value(device.secrets.get("readable_by_agent")),
        ),
        safety=SafetyBrief(
            sudo_requires_confirmation=bool_value(device.policy.get("require_confirm_for_sudo")),
            remote_exec_enabled=bool_value(device.policy.get("allow_remote_exec")),
        ),
    )
    assert_safe_output(brief.model_dump(mode="json"))
    return brief
