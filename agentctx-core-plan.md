# agentctx-core 方案

## 1. 目标

`agentctx-core` 是一个本机只读上下文解析器，用于解决跨项目、跨会话、跨设备时反复向 agent 解释项目、连接、SSH alias、远端路径、URL、容器名和注意事项的问题。

目标是让新 agent 能快速读取脱敏上下文，而不是依赖用户每次口述。

---

## 2. 非目标

`agentctx-core` v0 不做以下事情：

```text
MCP server
HTTP server
A2A
远程执行
自动部署
读取 .env 原文
读取 .pem 原文
读取 password 文件
暴露 secret 文件路径
```

---

## 3. 核心原则

```text
1. core 只负责解析上下文，不负责执行远程操作。
2. show 命令必须只读，无副作用。
3. use 命令才允许写入当前 workspace 的本地状态。
4. secret 只允许以 ref/status 形式存在，不允许输出原文或路径。
5. 输出采用 allowlist，不做“读全量后正则脱敏”。
6. 当前 target 优先使用命令行参数或环境变量，不依赖全局 active.env。
7. 项目公开事实放项目仓库，私有设备和绑定信息放用户本机。
```

---

## 4. 推荐目录结构

### 4.1 用户本机私有目录

```text
~/.agentctx/
  config.yaml

  devices/
    example-nas.yaml
    company-cloud.yaml

  bindings/
    sample-app.nas-test.yaml
    sample-app.cloud-prod.yaml

  secrets/
    example-nas/
      app.env
      db.env
      key.pem

  audit/
    agentctx.log.jsonl

  bin/
    agentctx.ps1
```

### 4.2 项目目录

```text
<project>/
  AGENTS.md

  .agent/
    project.yaml
    local.current.yaml

  docs/
    ops/
      DevServer_connection.md
```

### 4.3 `.gitignore`

```gitignore
.agent/local.current.yaml
.agent/local.yaml
.env
.env.*
*.pem
```

---

## 5. 数据模型

```text
Project
Device
Binding
Session
Policy
SecretRef
AuditEvent
```

---

## 6. Project

位置：

```text
<project>/.agent/project.yaml
```

可提交 Git。

示例：

```yaml
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
```

---

## 7. Device

位置：

```text
~/.agentctx/devices/example-nas.yaml
```

不提交 Git。

示例：

```yaml
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
```

禁止字段：

```yaml
password: xxx
token: xxx
private_key: xxx
password_path: <secret-file>
pem_path: <secret-file>
env_path: <secret-file>
```

---

## 8. Binding

位置：

```text
~/.agentctx/bindings/sample-app.nas-test.yaml
```

不提交 Git。

示例：

```yaml
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
  - 先在 NAS 验证，再同步云端
  - 远端路径包含中文和空格时必须加引号
  - rsync 必须排除 .env、node_modules、.next、.git
```

---

## 9. Session

位置：

```text
<project>/.agent/local.current.yaml
```

不提交 Git。

示例：

```yaml
schema: agentctx.session/v1

current_target: nas-test
permission_mode: read_context
```

target 解析优先级：

```text
1. 命令行参数：--target nas-test
2. 环境变量：AGENTCTX_TARGET
3. 当前项目本地状态：.agent/local.current.yaml
4. 项目默认值：.agent/project.yaml 的 default_target
```

---

## 10. 项目 AGENTS.md

位置：

```text
<project>/AGENTS.md
```

示例：

```md
# AGENTS.md

当任务涉及 NAS、企业存储、云服务器、远程部署、Docker、数据库、内网服务时：

1. 先运行：

   `agentctx show`

2. 如果需要指定环境，运行：

   `agentctx show --target nas-test`

3. 再读取：

   `docs/ops/DevServer_connection.md`

4. 不要读取、打印、复制：
   - `.env`
   - `.env.*`
   - `*.pem`
   - password 文件
   - token
   - JWT
   - service role key
   - 私钥内容

5. 优先使用 SSH alias，不要要求用户提供密码或私钥路径。

6. 涉及 sudo、生产环境、删除、数据库 reset、Docker volume 删除、force push 时，先给计划并等待用户确认。
```

---

## 11. DevServer_connection.md

位置：

```text
<project>/docs/ops/DevServer_connection.md
```

示例：

```md
# DevServer Connection

## nas-test

- SSH alias: example-nas
- Remote app dir: /vol1/@team/示例团队/示例用户/sample-app
- Remote supabase dir: /vol1/@team/示例团队/示例用户/sample-supabase
- App container: sample-app
- Postgres container: sample-postgres
- Reverse proxy container: sample-reverse-proxy
- Deploy requires sudo: yes

## Sudo rules

- 查看 docker 状态一般不需要 sudo。
- `docker compose up -d` 在 NAS 上可能需要 sudo。
- 修改系统服务、Nginx、挂载目录权限必须先确认。

## Known pitfalls

- 不要执行 `docker compose down -v`。
- 不要在 NAS 测试环境执行 `supabase db reset`。
- rsync 必须排除 `.env`、`node_modules`、`.next`、`.git`。
- 远端路径包含中文和空格时必须加引号。
```

---

## 12. CLI 命令

### 12.1 `agentctx show`

只读输出当前上下文。

```powershell
agentctx show
```

指定 target：

```powershell
agentctx show --target nas-test
```

指定项目和 target：

```powershell
agentctx show --project sample-app --target nas-test
```

### 12.2 `agentctx list`

列出当前项目可用 target。

```powershell
agentctx list
```

输出示例：

```text
local-dev
nas-test
cloud-prod
```

### 12.3 `agentctx use`

写入当前 workspace 的本地 session。

```powershell
agentctx use nas-test
```

写入：

```text
<project>/.agent/local.current.yaml
```

### 12.4 `agentctx doctor`

检查配置完整性和安全风险。

```powershell
agentctx doctor
```

检查项：

```text
.agent/project.yaml 是否存在
docs/ops/DevServer_connection.md 是否存在
.agent/local.current.yaml 是否被 gitignore
target 是否能解析到 binding
binding 是否能解析到 device
device/binding/project 中是否出现疑似 secret 字段
show 输出是否包含疑似 secret
SSH alias 是否存在于 device 配置
```

---

## 13. `agentctx show` 输出格式

```text
Agent Context Brief
===================

Project:
  id: sample-app
  name: 示例项目
  workspace: <workspace>/sample-app

Target:
  id: nas-test
  kind: nas
  risk: medium

Connection:
  device: example-nas
  ssh alias: example-nas
  app url: http://192.0.2.10:8080
  direct url: http://192.0.2.10:8767

Remote:
  app dir: /vol1/@team/示例团队/示例用户/sample-app
  supabase dir: /vol1/@team/示例团队/示例用户/sample-supabase

Containers:
  app: sample-app
  postgres: sample-postgres
  reverse proxy: sample-reverse-proxy

Docs:
  devserver connection: docs/ops/DevServer_connection.md
  deployment: docs/ops/NAS_DEPLOYMENT.md

Secrets:
  configured: yes
  readable by agent: no
  policy: use SSH alias / configured credentials only

Safety:
  sudo requires confirmation: yes
  remote exec enabled: no
  prod requires confirmation: yes
  forbidden:
    - docker compose down -v
    - supabase db reset
    - rm -rf on remote paths
```

---

## 14. 输出 allowlist

允许输出：

```text
project_id
project_name
workspace
target_id
target_kind
risk
device_id
ssh_alias
app_url
app_direct_url
remote_app_dir
remote_supabase_dir
container_names
docs paths
sudo policy
forbidden_commands
secret configured yes/no
secret readable_by_agent false
```

禁止输出：

```text
password
token
JWT
service role key
private key
private key path
.env 原文
.env 文件路径
.pem 原文
.pem 文件路径
secret 文件绝对路径
```

---

## 15. 核心函数

```text
load_project(workspace) -> Project

load_device(device_id) -> Device

load_binding(binding_id) -> Binding

load_session(workspace) -> Session

resolve_target(cli_target, env_target, session_target, project_default) -> target_id

resolve_context(workspace, project_id, target_id) -> ContextBrief

render_brief(context, format) -> string

check_policy(project_id, target_id, action) -> PolicyDecision

doctor(workspace) -> DoctorReport

audit(event) -> void
```

---

## 16. 解析流程

```text
1. 从当前目录向上查找 .agent/project.yaml
2. 读取 Project
3. 按优先级确定 target
4. 根据 target 找到 binding id
5. 读取 ~/.agentctx/bindings/<binding>.yaml
6. 根据 binding.device_id 读取 ~/.agentctx/devices/<device>.yaml
7. 合并 Project + Target + Binding + Device
8. 只保留 allowlist 字段
9. 检查输出中是否含疑似 secret
10. 渲染为 text / markdown / json
11. 写入 audit log
```

---

## 17. 安全检查

疑似 secret 字段名：

```text
password
passwd
pwd
token
secret
jwt
service_role
private_key
apikey
api_key
access_key
refresh_token
client_secret
```

疑似 secret 内容：

```text
-----BEGIN PRIVATE KEY-----
-----BEGIN RSA PRIVATE KEY-----
eyJ
sk-
ghp_
xoxb-
AKIA
```

处理规则：

```text
1. 配置文件中出现疑似 secret 字段：doctor 警告。
2. show 输出中出现疑似 secret：直接失败，不输出 brief。
3. device.secrets 下只允许 configured/readable_by_agent/*_ref，不允许原文和路径。
4. readable_by_agent 必须为 false。
```

---

## 18. 审计日志

位置：

```text
~/.agentctx/audit/agentctx.log.jsonl
```

示例：

```json
{"ts":"2026-06-27T10:00:00+09:00","cmd":"show","project":"sample-app","target":"nas-test","result":"ok"}
{"ts":"2026-06-27T10:02:00+09:00","cmd":"doctor","project":"sample-app","result":"warning","warnings":2}
```

---

## 19. v0 实现边界

v0 必须实现：

```text
agentctx show
agentctx show --target <target>
agentctx list
agentctx use <target>
agentctx doctor
text 输出
json 输出
secret 字段检查
```

v0 可以暂缓：

```text
MCP
HTTP server
A2A
远程执行
审批流
团队权限
多用户 RBAC
真实 secret manager 集成
```

---

## 20. 推荐实现结构

```text
agentctx/
  pyproject.toml

  src/
    agentctx/
      __init__.py
      cli.py

      core/
        loader.py
        resolver.py
        sanitizer.py
        renderer.py
        policy.py
        doctor.py
        audit.py

      schemas/
        project.schema.json
        device.schema.json
        binding.schema.json
        session.schema.json

  tests/
    test_loader.py
    test_resolver.py
    test_sanitizer.py
    test_policy.py
    test_doctor.py
```

---

## 21. v0 验收标准

```text
1. 在任意项目目录运行 agentctx show，可以自动找到 .agent/project.yaml。
2. 不传 --target 时，能按优先级解析当前 target。
3. 传 --target nas-test 时，能覆盖本地 session。
4. show 输出包含项目、target、SSH alias、远端路径、URL、容器名、安全规则。
5. show 输出不包含 password/token/private key/.env/.pem 路径或原文。
6. agentctx use nas-test 只写 .agent/local.current.yaml。
7. agentctx doctor 能发现未 gitignore 的 local.current.yaml。
8. 同一项目不同终端可用 AGENTCTX_TARGET 指定不同 target，互不污染。
9. 缺少 binding/device/project 时给出明确错误。
10. JSON 输出可被后续 MCP adapter 直接复用。
```
