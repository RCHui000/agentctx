from __future__ import annotations

import json

from agentctx.core.models import ContextBrief, DoctorReport, ServerBrief


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_brief_text(context: ContextBrief) -> str:
    lines = [
        "Agent Context Brief",
        "===================",
        "",
        "Project:",
        f"  id: {context.project.id}",
        f"  name: {context.project.name}",
        f"  workspace: {context.project.workspace}",
        "",
        "Target:",
        f"  id: {context.target.id}",
        f"  kind: {context.target.kind}",
        f"  risk: {context.target.risk}",
    ]
    if context.connection.device or context.connection.ssh_alias:
        lines.extend(
            [
                "",
                "Connection:",
                f"  device: {context.connection.device or ''}",
                f"  host: {context.connection.host or ''}",
                f"  ssh alias: {context.connection.ssh_alias or ''}",
                f"  app url: {context.connection.app_url or ''}",
                f"  direct url: {context.connection.app_direct_url or ''}",
            ]
        )
    if context.remote.app_dir or context.remote.supabase_dir:
        lines.extend(
            [
                "",
                "Remote:",
                f"  app dir: {context.remote.app_dir or ''}",
                f"  supabase dir: {context.remote.supabase_dir or ''}",
            ]
        )
    if context.containers.app or context.containers.postgres or context.containers.reverse_proxy:
        lines.extend(
            [
                "",
                "Containers:",
                f"  app: {context.containers.app or ''}",
                f"  postgres: {context.containers.postgres or ''}",
                f"  reverse proxy: {context.containers.reverse_proxy or ''}",
            ]
        )
    if context.docs:
        lines.append("")
        lines.append("Docs:")
        for label, path in context.docs.items():
            lines.append(f"  {label.replace('_', ' ')}: {path}")
    lines.extend(
        [
            "",
            "Secrets:",
            f"  configured: {yes_no(context.secrets.configured)}",
            f"  readable by agent: {yes_no(context.secrets.readable_by_agent)}",
            f"  policy: {context.secrets.policy}",
            "",
            "Safety:",
            f"  sudo requires confirmation: {yes_no(context.safety.sudo_requires_confirmation)}",
            f"  remote exec enabled: {yes_no(context.safety.remote_exec_enabled)}",
            f"  prod requires confirmation: {yes_no(context.safety.prod_requires_confirmation)}",
        ]
    )
    if context.safety.forbidden:
        lines.append("  forbidden:")
        for command in context.safety.forbidden:
            lines.append(f"    - {command}")
    return "\n".join(lines) + "\n"


def render_brief_json(context: ContextBrief) -> str:
    return json.dumps(context.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2) + "\n"


def render_server_text(server: ServerBrief) -> str:
    lines = [
        "Agent Server Brief",
        "==================",
        "",
        "Device:",
        f"  id: {server.device.id}",
        f"  kind: {server.device.kind}",
        f"  display name: {server.device.display_name or ''}",
        "",
        "Connection:",
        f"  host: {server.connection.host or ''}",
        f"  ssh alias: {server.connection.ssh_alias or ''}",
        f"  app url: {server.connection.app_url or ''}",
        f"  direct url: {server.connection.app_direct_url or ''}",
        "",
        "Secrets:",
        f"  configured: {yes_no(server.secrets.configured)}",
        f"  readable by agent: {yes_no(server.secrets.readable_by_agent)}",
        f"  policy: {server.secrets.policy}",
        "",
        "Safety:",
        f"  sudo requires confirmation: {yes_no(server.safety.sudo_requires_confirmation)}",
        f"  remote exec enabled: {yes_no(server.safety.remote_exec_enabled)}",
    ]
    return "\n".join(lines) + "\n"


def render_server_json(server: ServerBrief) -> str:
    return json.dumps(server.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"


def render_doctor(report: DoctorReport) -> str:
    lines = [f"Doctor result: {report.result}"]
    if report.errors:
        lines.append("")
        lines.append("Errors:")
        for item in report.errors:
            suffix = f" ({item.path})" if item.path else ""
            lines.append(f"  - {item.message}{suffix}")
    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for item in report.warnings:
            suffix = f" ({item.path})" if item.path else ""
            lines.append(f"  - {item.message}{suffix}")
    return "\n".join(lines) + "\n"
