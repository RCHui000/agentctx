from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    workspace = tmp_path / "workspace with spaces 项目"
    agent_home = tmp_path / "agent home 私有"
    workspace.mkdir(parents=True)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("AGENTCTX_HOME", str(agent_home))

    write_text(
        workspace / ".agent" / "project.yaml",
        """
        schema: agentctx.project/v1
        project_id: sample-app
        name: 示例项目
        docs:
          devserver_connection: docs/ops/DevServer_connection.md
          deployment: docs/ops/NAS_DEPLOYMENT.md
        default_target: nas-test
        targets:
          local-dev:
            kind: local
            risk: low
          nas-test:
            kind: nas
            binding: sample-app.nas-test
            risk: medium
          cloud-prod:
            kind: cloud
            binding: sample-app.cloud-prod
            risk: high
            require_confirm: true
        """,
    )
    write_text(
        workspace / ".agent" / "local.current.yaml",
        """
        schema: agentctx.session/v1
        current_target: local-dev
        permission_mode: read_context
        """,
    )
    write_text(
        workspace / ".gitignore",
        """
        .agent/local.current.yaml
        .agent/local.yaml
        .env
        .env.*
        *.pem
        """,
    )
    write_text(
        workspace / "docs" / "ops" / "DevServer_connection.md",
        "# DevServer Connection\n",
    )
    write_text(
        agent_home / "bindings" / "sample-app.nas-test.yaml",
        """
        schema: agentctx.binding/v1
        binding_id: sample-app.nas-test
        project_id: sample-app
        target_id: nas-test
        device_id: example-nas
        remote:
          app_dir: /vol1/@team/示例团队/示例用户/sample-app
          supabase_dir: /vol1/@team/示例团队/示例用户/sample-supabase
        containers:
          app: sample-app
          postgres: sample-postgres
          reverse_proxy: sample-reverse-proxy
        deploy:
          strategy: rsync_then_compose
          requires_sudo: true
          remote_exec_enabled: false
        forbidden_commands:
          - docker compose down -v
          - supabase db reset
          - rm -rf on remote paths
        notes:
          - 远端路径包含中文和空格时必须加引号
        """,
    )
    write_text(
        agent_home / "bindings" / "sample-app.cloud-prod.yaml",
        """
        schema: agentctx.binding/v1
        binding_id: sample-app.cloud-prod
        project_id: sample-app
        target_id: cloud-prod
        device_id: example-nas
        remote:
          app_dir: /srv/sample-app
        containers:
          app: sample-app
        deploy:
          requires_sudo: true
          remote_exec_enabled: false
        forbidden_commands:
          - docker compose down -v
        """,
    )
    write_text(
        agent_home / "devices" / "example-nas.yaml",
        """
        schema: agentctx.device/v1
        device_id: example-nas
        kind: nas
        display_name: 办公室 NAS
        ssh:
          alias: example-nas
          auth: ssh-config
          credential_ref: ssh-config:example-nas
        network:
          app_url: http://192.0.2.10:8080
          app_direct_url: http://192.0.2.10:8767
          gotrue_url: http://192.0.2.10:8777
          postgrest_url: http://192.0.2.10:8779
        secrets:
          configured: true
          readable_by_agent: false
          env_ref: agentctx-secret:example-nas/app-env
          ssh_key_ref: ssh-config:example-nas
        policy:
          allow_read_context: true
          allow_remote_exec: false
          require_confirm_for_sudo: true
          require_confirm_for_delete: true
        """,
    )
    return {"workspace": workspace, "agent_home": agent_home}
