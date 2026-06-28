# agentctx-core v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-first Python CLI that resolves local agent context from project, binding, device, and session YAML files without exposing secrets.

**Architecture:** The CLI delegates all behavior to small core modules: loaders read YAML from the workspace and user config root, the resolver builds a sanitized context brief, renderers output text or JSON, and doctor reports configuration and safety issues. Tests construct temporary workspaces and user config roots so no real user secrets or machine config are read.

**Tech Stack:** Python 3.11+, Typer, Pydantic, PyYAML, pytest.

---

### Task 1: Project Skeleton And Tests

**Files:**
- Create: `pyproject.toml`
- Create: `src/agentctx/__init__.py`
- Create: `src/agentctx/cli.py`
- Create: `src/agentctx/core/*.py`
- Create: `tests/conftest.py`
- Create: `tests/test_resolver.py`
- Create: `tests/test_cli.py`
- Create: `tests/test_doctor.py`

- [x] Write fixtures that create `.agent/project.yaml`, `.agent/local.current.yaml`, private bindings, and private devices under a temporary `AGENTCTX_HOME`.
- [x] Add failing tests for target precedence, show/list/use/doctor, JSON output, text output, Chinese paths, and secret blocking.
- [x] Run `python -m pytest` and verify failures come from missing implementation.

### Task 2: Core Context Resolution

**Files:**
- Modify: `src/agentctx/core/models.py`
- Modify: `src/agentctx/core/loader.py`
- Modify: `src/agentctx/core/resolver.py`
- Modify: `src/agentctx/core/sanitizer.py`

- [x] Implement Pydantic models for project, device, binding, session, context brief, and doctor reports.
- [x] Implement upward workspace discovery for `.agent/project.yaml`.
- [x] Implement target precedence: CLI target, `AGENTCTX_TARGET`, local session, project default.
- [x] Implement allowlist-only context assembly and secret scanning.
- [x] Run resolver and sanitizer tests.

### Task 3: CLI, Rendering, Session Writes, Audit, Doctor

**Files:**
- Modify: `src/agentctx/cli.py`
- Modify: `src/agentctx/core/renderer.py`
- Modify: `src/agentctx/core/doctor.py`
- Modify: `src/agentctx/core/audit.py`

- [x] Implement `agentctx show --target <id> --format text|json`.
- [x] Implement `agentctx list`.
- [x] Implement `agentctx use <target>` writing only `.agent/local.current.yaml`.
- [x] Implement `agentctx doctor` with missing config, gitignore, and secret checks.
- [x] Implement audit JSONL records without context details.
- [x] Run CLI and doctor tests.

### Task 4: Verification And Commit

**Files:**
- All implementation files

- [x] Run `python -m pytest`.
- [x] Run CLI smoke checks with temp fixtures through pytest.
- [x] Run `git diff --check`.
- [x] Stage and commit the completed v0 implementation.
