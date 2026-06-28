from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentctx.core.audit import audit_event
from agentctx.core.doctor import run_doctor
from agentctx.core.loader import ConfigLoadError, get_agent_home, list_devices, load_project, write_session
from agentctx.core.renderer import render_brief_json, render_brief_text, render_doctor, render_server_json, render_server_text
from agentctx.core.resolver import ContextResolutionError, resolve_context
from agentctx.core.sanitizer import UnsafeContextError
from agentctx.core.server import resolve_server


app = typer.Typer(add_completion=False, no_args_is_help=True)
server_app = typer.Typer(help="Discover global server/NAS connection briefs.")
app.add_typer(server_app, name="server")


def _fail(message: str) -> None:
    typer.echo(message)
    raise typer.Exit(1)


@app.command()
def show(
    target: Annotated[str | None, typer.Option("--target", help="Target id to use.")] = None,
    output_format: Annotated[str, typer.Option("--format", help="Output format: text or json.")] = "text",
    project: Annotated[str | None, typer.Option("--project", help="Validate the current project id.")] = None,
) -> None:
    home = get_agent_home()
    try:
        context = resolve_context(Path.cwd(), home, cli_target=target, project_id=project)
        if output_format == "text":
            typer.echo(render_brief_text(context), nl=False)
        elif output_format == "json":
            typer.echo(render_brief_json(context), nl=False)
        else:
            _fail(f"Unsupported format: {output_format}")
        audit_event("show", project=context.project.id, target=context.target.id, result="ok", agent_home=home)
    except (ConfigLoadError, ContextResolutionError, UnsafeContextError) as exc:
        audit_event("show", target=target, result="error", errors=1, agent_home=home)
        _fail(str(exc))


@app.command("list")
def list_targets() -> None:
    home = get_agent_home()
    try:
        _root, project = load_project(Path.cwd())
    except ConfigLoadError as exc:
        audit_event("list", result="error", errors=1, agent_home=home)
        _fail(str(exc))
    for target_id in project.targets:
        typer.echo(target_id)
    audit_event("list", project=project.project_id, result="ok", agent_home=home)


@app.command()
def use(target: str) -> None:
    home = get_agent_home()
    try:
        root, project = load_project(Path.cwd())
    except ConfigLoadError as exc:
        audit_event("use", target=target, result="error", errors=1, agent_home=home)
        _fail(str(exc))
    if target not in project.targets:
        audit_event("use", project=project.project_id, target=target, result="error", errors=1, agent_home=home)
        _fail(f"Unknown target: {target}")
    path = write_session(root, target)
    typer.echo(f"Current target set to {target} in {path}")
    audit_event("use", project=project.project_id, target=target, result="ok", agent_home=home)


@app.command()
def doctor() -> None:
    home = get_agent_home()
    report = run_doctor(Path.cwd(), home)
    typer.echo(render_doctor(report), nl=False)
    audit_event(
        "doctor",
        result=report.result,
        warnings=len(report.warnings),
        errors=len(report.errors),
        agent_home=home,
    )
    if report.result == "error":
        raise typer.Exit(1)


@server_app.command("list")
def server_list() -> None:
    home = get_agent_home()
    for device_id in list_devices(home):
        typer.echo(device_id)
    audit_event("server list", result="ok", agent_home=home)


@server_app.command("show")
def server_show(
    device_id: str,
    output_format: Annotated[str, typer.Option("--format", help="Output format: text or json.")] = "text",
) -> None:
    home = get_agent_home()
    try:
        server = resolve_server(device_id, home)
        if output_format == "text":
            typer.echo(render_server_text(server), nl=False)
        elif output_format == "json":
            typer.echo(render_server_json(server), nl=False)
        else:
            _fail(f"Unsupported format: {output_format}")
        audit_event("server show", target=device_id, result="ok", agent_home=home)
    except (ConfigLoadError, UnsafeContextError) as exc:
        audit_event("server show", target=device_id, result="error", errors=1, agent_home=home)
        _fail(str(exc))
