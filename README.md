# agentctx-core

`agentctx-core` 是一个 Windows 优先的 Python CLI，用来让 agent 在本机安全发现项目、target、NAS/服务器、SSH alias、远端路径、容器名和安全注意事项。

它的目标是减少反复口述上下文，同时避免把密码、token、`.env`、私钥或 secret 文件路径暴露给 agent。

## 核心边界

- `agentctx` 只做上下文发现，不做远程执行、部署、审批流、HTTP 服务或 MCP 服务。
- 输出采用 allowlist，只渲染安全字段。
- secret 只能以状态或引用形式存在，例如 `configured: true`、`readable_by_agent: false`、`ssh-config:example-nas`。
- 如果渲染前发现疑似 secret 字段或内容，`show` / `server show` 会拒绝输出 brief。

## 安装

需要 Python 3.11+。

```powershell
python -m pip install -e .[dev]
```

安装后可运行：

```powershell
agentctx --help
```

## 常用命令

```powershell
agentctx show
agentctx show --target nas-test
agentctx show --target nas-test --format json
agentctx list
agentctx use nas-test
agentctx doctor
```

全局设备发现不依赖当前项目目录：

```powershell
agentctx server list
agentctx server show example-nas
agentctx server show example-nas --format json
```

## 配置结构

项目仓库只提交公开事实：

```text
<project>/
  .agent/
    project.yaml
```

用户本机保存私有设备和项目绑定：

```text
~/.agentctx/
  devices/
    example-nas.yaml
  bindings/
    sample-app.nas-test.yaml
  audit/
    agentctx.log.jsonl
```

`.agent/local.current.yaml` 是当前 workspace 的本地状态，应加入 `.gitignore`。

## 最小示例

`.agent/project.yaml`：

```yaml
schema: agentctx.project/v1
project_id: sample-app
name: 示例项目
default_target: nas-test
targets:
  local-dev:
    kind: local
    risk: low
  nas-test:
    kind: nas
    binding: sample-app.nas-test
    risk: medium
```

`~/.agentctx/devices/example-nas.yaml`：

```yaml
schema: agentctx.device/v1
device_id: example-nas
kind: nas
display_name: 示例 NAS
ssh:
  alias: example-nas
  auth: ssh-config
  credential_ref: ssh-config:example-nas
network:
  app_url: http://192.0.2.10:8080
secrets:
  configured: true
  readable_by_agent: false
  ssh_key_ref: ssh-config:example-nas
policy:
  allow_read_context: true
  allow_remote_exec: false
  require_confirm_for_sudo: true
```

`~/.agentctx/bindings/sample-app.nas-test.yaml`：

```yaml
schema: agentctx.binding/v1
binding_id: sample-app.nas-test
project_id: sample-app
target_id: nas-test
device_id: example-nas
remote:
  app_dir: /srv/sample-app
containers:
  app: sample-app
forbidden_commands:
  - docker compose down -v
```

## Target 解析优先级

1. CLI 参数：`--target <id>`
2. 环境变量：`AGENTCTX_TARGET`
3. 当前项目本地状态：`.agent/local.current.yaml`
4. 项目默认值：`.agent/project.yaml` 的 `default_target`

## 安全规则

- 不要在 YAML 中存 raw password、token、JWT、private key、`.env` 原文、`.pem` 原文或 secret 文件路径。
- 优先存 SSH alias、credential reference、key reference。
- `agentctx doctor` 用于检查配置完整性和疑似 secret 风险。
- 审计日志只记录命令、项目、target、结果和 warning/error 数量，不记录上下文详情。

## 开发验证

```powershell
python -m pytest
git diff --check
```
