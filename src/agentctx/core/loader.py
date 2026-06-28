from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from agentctx.core.models import Binding, Device, Project, Session


class ConfigLoadError(RuntimeError):
    pass


def get_agent_home(agent_home: Path | str | None = None) -> Path:
    if agent_home is not None:
        return Path(agent_home)
    env_home = os.environ.get("AGENTCTX_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".agentctx"


def find_project_root(start: Path | str | None = None) -> Path:
    current = Path.cwd() if start is None else Path(start)
    current = current.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".agent" / "project.yaml").exists():
            return candidate
    raise ConfigLoadError(f"Could not find .agent/project.yaml from {current}")


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigLoadError(f"Missing config file: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigLoadError(f"Expected YAML mapping in {path}")
    return loaded


def load_project(workspace: Path | str | None = None) -> tuple[Path, Project]:
    root = find_project_root(workspace)
    return root, Project.model_validate(read_yaml(root / ".agent" / "project.yaml"))


def load_session(workspace: Path | str) -> Session | None:
    path = Path(workspace) / ".agent" / "local.current.yaml"
    if not path.exists():
        return None
    return Session.model_validate(read_yaml(path))


def load_binding(agent_home: Path | str, binding_id: str) -> Binding:
    path = Path(agent_home) / "bindings" / f"{binding_id}.yaml"
    return Binding.model_validate(read_yaml(path))


def load_device(agent_home: Path | str, device_id: str) -> Device:
    path = Path(agent_home) / "devices" / f"{device_id}.yaml"
    return Device.model_validate(read_yaml(path))


def list_devices(agent_home: Path | str) -> list[str]:
    devices_dir = Path(agent_home) / "devices"
    if not devices_dir.exists():
        return []
    return sorted(path.stem for path in devices_dir.glob("*.yaml") if path.is_file())


def write_session(workspace: Path | str, target_id: str) -> Path:
    path = Path(workspace) / ".agent" / "local.current.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "agentctx.session/v1",
        "current_target": target_id,
        "permission_mode": "read_context",
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path
