from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class AgentCtxModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class TargetConfig(AgentCtxModel):
    kind: str
    risk: str = "unknown"
    binding: str | None = None
    require_confirm: bool = False


class Project(AgentCtxModel):
    schema_: str = Field(alias="schema")
    project_id: str
    name: str
    docs: dict[str, str] = Field(default_factory=dict)
    default_target: str | None = None
    targets: dict[str, TargetConfig] = Field(default_factory=dict)


class Session(AgentCtxModel):
    schema_: str = Field(alias="schema")
    current_target: str | None = None
    permission_mode: str | None = None


class Binding(AgentCtxModel):
    schema_: str = Field(alias="schema")
    binding_id: str
    project_id: str
    target_id: str
    device_id: str | None = None
    remote: dict[str, str] = Field(default_factory=dict)
    containers: dict[str, str] = Field(default_factory=dict)
    deploy: dict[str, object] = Field(default_factory=dict)
    forbidden_commands: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Device(AgentCtxModel):
    schema_: str = Field(alias="schema")
    device_id: str
    kind: str
    display_name: str | None = None
    ssh: dict[str, object] = Field(default_factory=dict)
    network: dict[str, object] = Field(default_factory=dict)
    secrets: dict[str, object] = Field(default_factory=dict)
    policy: dict[str, object] = Field(default_factory=dict)


class ProjectBrief(AgentCtxModel):
    id: str
    name: str
    workspace: str
    docs: dict[str, str] = Field(default_factory=dict)


class TargetBrief(AgentCtxModel):
    id: str
    kind: str
    risk: str
    require_confirm: bool = False


class ConnectionBrief(AgentCtxModel):
    device: str | None = None
    host: str | None = None
    ssh_alias: str | None = None
    app_url: str | None = None
    app_direct_url: str | None = None


class RemoteBrief(AgentCtxModel):
    app_dir: str | None = None
    supabase_dir: str | None = None


class ContainersBrief(AgentCtxModel):
    app: str | None = None
    postgres: str | None = None
    reverse_proxy: str | None = None


class SecretsBrief(AgentCtxModel):
    configured: bool = False
    readable_by_agent: bool = False
    policy: str = "use SSH alias / configured credentials only"


class SafetyBrief(AgentCtxModel):
    sudo_requires_confirmation: bool = False
    remote_exec_enabled: bool = False
    prod_requires_confirmation: bool = False
    forbidden: list[str] = Field(default_factory=list)


class ContextBrief(AgentCtxModel):
    project: ProjectBrief
    target: TargetBrief
    connection: ConnectionBrief = Field(default_factory=ConnectionBrief)
    remote: RemoteBrief = Field(default_factory=RemoteBrief)
    containers: ContainersBrief = Field(default_factory=ContainersBrief)
    docs: dict[str, str] = Field(default_factory=dict)
    secrets: SecretsBrief = Field(default_factory=SecretsBrief)
    safety: SafetyBrief = Field(default_factory=SafetyBrief)


class DeviceBrief(AgentCtxModel):
    id: str
    kind: str
    display_name: str | None = None


class ServerBrief(AgentCtxModel):
    device: DeviceBrief
    connection: ConnectionBrief = Field(default_factory=ConnectionBrief)
    secrets: SecretsBrief = Field(default_factory=SecretsBrief)
    safety: SafetyBrief = Field(default_factory=SafetyBrief)


class DoctorItem(AgentCtxModel):
    message: str
    path: str | None = None


class DoctorReport(AgentCtxModel):
    result: str
    errors: list[DoctorItem] = Field(default_factory=list)
    warnings: list[DoctorItem] = Field(default_factory=list)


def path_text(path: Path) -> str:
    return str(path)
