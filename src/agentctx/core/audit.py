from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from agentctx.core.loader import get_agent_home


def audit_event(
    cmd: str,
    *,
    project: str | None = None,
    target: str | None = None,
    result: str,
    warnings: int = 0,
    errors: int = 0,
    agent_home: Path | str | None = None,
) -> None:
    home = get_agent_home(agent_home)
    path = home / "audit" / "agentctx.log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cmd": cmd,
        "project": project,
        "target": target,
        "result": result,
        "warnings": warnings,
        "errors": errors,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({k: v for k, v in event.items() if v is not None}, ensure_ascii=False) + "\n")
