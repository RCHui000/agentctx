from __future__ import annotations

from pathlib import Path
from typing import Any

from agentctx.core.loader import ConfigLoadError, get_agent_home, load_binding, load_device, load_project, read_yaml
from agentctx.core.models import DoctorItem, DoctorReport
from agentctx.core.resolver import ContextResolutionError, resolve_context
from agentctx.core.sanitizer import (
    find_suspicious_keys,
    find_suspicious_values,
    validate_device_secret_block,
)


def _add_items(items: list[DoctorItem], messages: list[str], path: Path) -> None:
    for message in messages:
        items.append(DoctorItem(message=f"Suspicious secret field or value: {message}", path=str(path)))


def _scan_yaml(path: Path, warnings: list[DoctorItem]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = read_yaml(path)
    except ConfigLoadError as exc:
        warnings.append(DoctorItem(message=str(exc), path=str(path)))
        return None
    _add_items(warnings, find_suspicious_keys(data) + find_suspicious_values(data), path)
    return data


def _gitignore_contains(workspace: Path, pattern: str) -> bool:
    gitignore = workspace / ".gitignore"
    if not gitignore.exists():
        return False
    lines = [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()]
    return pattern in lines


def run_doctor(workspace: Path | str | None = None, agent_home: Path | str | None = None) -> DoctorReport:
    errors: list[DoctorItem] = []
    warnings: list[DoctorItem] = []
    home = get_agent_home(agent_home)

    try:
        root, project = load_project(workspace)
    except ConfigLoadError as exc:
        return DoctorReport(result="error", errors=[DoctorItem(message=str(exc))])

    project_path = root / ".agent" / "project.yaml"
    _scan_yaml(project_path, warnings)

    devserver_doc = project.docs.get("devserver_connection")
    if devserver_doc and not (root / devserver_doc).exists():
        errors.append(DoctorItem(message=f"Missing docs file: {devserver_doc}", path=str(root / devserver_doc)))

    local_session_path = root / ".agent" / "local.current.yaml"
    if local_session_path.exists() and not _gitignore_contains(root, ".agent/local.current.yaml"):
        warnings.append(DoctorItem(message=".agent/local.current.yaml is not gitignored", path=str(root / ".gitignore")))
    _scan_yaml(local_session_path, warnings)

    for target_id, target in project.targets.items():
        if not target.binding:
            continue
        binding_path = home / "bindings" / f"{target.binding}.yaml"
        binding_data = _scan_yaml(binding_path, warnings)
        try:
            binding = load_binding(home, target.binding)
        except ConfigLoadError as exc:
            errors.append(DoctorItem(message=f"Missing binding {target.binding} for target {target_id}: {exc}", path=str(binding_path)))
            continue
        if binding.project_id != project.project_id:
            errors.append(DoctorItem(message=f"Binding {binding.binding_id} points at project {binding.project_id}", path=str(binding_path)))
        if binding.target_id != target_id:
            errors.append(DoctorItem(message=f"Binding {binding.binding_id} points at target {binding.target_id}", path=str(binding_path)))
        if binding_data is None:
            continue
        if not binding.device_id:
            errors.append(DoctorItem(message=f"Binding {binding.binding_id} has no device_id", path=str(binding_path)))
            continue
        device_path = home / "devices" / f"{binding.device_id}.yaml"
        device_data = _scan_yaml(device_path, warnings)
        try:
            device = load_device(home, binding.device_id)
        except ConfigLoadError as exc:
            errors.append(DoctorItem(message=f"Missing device {binding.device_id} for binding {binding.binding_id}: {exc}", path=str(device_path)))
            continue
        for warning in validate_device_secret_block(device.secrets):
            warnings.append(DoctorItem(message=warning, path=str(device_path)))
        if device_data and isinstance(device_data.get("secrets"), dict):
            for warning in validate_device_secret_block(device_data["secrets"]):
                warnings.append(DoctorItem(message=warning, path=str(device_path)))

    try:
        resolve_context(root, home)
    except ContextResolutionError as exc:
        errors.append(DoctorItem(message=str(exc)))
    except Exception as exc:
        errors.append(DoctorItem(message=str(exc)))

    if errors:
        result = "error"
    elif warnings:
        result = "warning"
    else:
        result = "ok"
    return DoctorReport(result=result, errors=errors, warnings=warnings)
