# 跨Agent协调模式

> 在同一台 Windows 机器上运行多个异构 AI Agent（Hermes、OpenClaw、Claude Code、Codex、MiMo），通过共享知识仓库和文件级消息队列实现跨 Agent 的知识沉淀、任务协作和经验复用，避免各 Agent 之间信息孤岛，形成可积累、可检索、可版本化的集体记忆系统。

## 核心组件

## 1. Agent 层 — 五个异构 Agent

| Agent | 运行位置 | 模型 | 职责 |
|-------|----------|------|------|
| **Hermes** | WSL | DeepSeek v4 Pro | 主调度节点、全平台消息网关 |
| **OpenClaw** | Windows | Doubao Pro | 企微/钉钉聊天对话 Agent |
| **Claude Code** | WSL | MiMo v2.5 Pro | 代码开发代理 |
| **Codex** | WSL | DeepSeek | 代码生成代理 |
| **MiMo Code** | WSL | MiMo v2.5 Pro | 终端 AI 编程助手 |

## 2. 共享知识仓库 — `C:\Users\zhaot\claude-memory\shared-knowledge\`

| 子目录 / 文件 | 用途 |
|----------------|------|
| `archives/` | 跨 Agent 知识沉淀（决策记录、架构文档） |
| `projects/` | 各项目共享上下文 |
| `workflows/` | 跨 Agent 工作流定义 |
| `cross-agent-rules.md` | 本文件 — 所有 Agent **启动时必须读取** |

## 3. 消息队列 — `C:\Users\zhaot\claude-memory\agent-messages\`

以文件为单位的异步消息通道：
- `*name*-to-hermes.md` / `*name*-to-openclaw.md` / `*name*-to-claude-code.md` / `*name*-to-mimo.md` — 发送给目标 Agent
- `hermes-to-*name*.md` — Hermes 的回复通道

## 4. Git 版本控制层

仓库 `~/claude-memory/` 统一管理所有共享文件和消息，提供变更历史与回滚能力。代理配置 `http://127.0.0.1:7897`。

## 5. 能力目录清单

各 Agent 启动时读取的清单文件，定位已有脚本、工作流、工具，防止重复造轮子。通过 `catalog/scripts/` 和 `catalog/skills/` 目录规范组织。

## 数据流

## 1. 启动阶段（每个 Agent 启动时）

```
Agent 启动
  → git pull ~/claude-memory/ (获取最新共享知识)
  → 读取 cross-agent-rules.md (知晓兄弟Agent存在、通讯方式、规则)
  → 读取能力目录 (检查已有脚本/工作流)
  → 进入正常任务循环
```

## 2. 知识沉淀阶段（发现新知识/踩坑/优化）

```
Agent 发现新知识/踩坑/优化
  → 写入跨 Agent 共享仓库 (archives/ / workflows/ / 本文件)
  → 更新能力目录索引
  → git add + git commit + git push (持久化)
  → 双重保存：本地记忆 + 共享仓库
```

## 3. Agent 间协作阶段（需要兄弟帮忙）

```
Agent A 需要兄弟 Agent B 帮助
  → 写文件 agent-a-to-agent-b.md 到 agent-messages/ 目录
  → (Agent B 下次启动或轮询时读到消息)
  → Agent B 处理任务
  → (Hermes 回复) 写文件 hermes-to-agent-a.md
  → Agent A 读到回复 → 继续执行
```

## 4. 知识复用阶段（开始新任务前）

```
Agent 接到新任务
  → 先查询共享仓库 (是否有现成脚本/工作流/工具)
  → 找到 → 直接复用
  → 没找到 → 新建，完成后走知识沉淀阶段

## 关键设计决策

1. **文件级消息队列而非网络 RPC** — Agent 之间通过写 .md 文件通讯，不引入消息中间件（如 RabbitMQ/Kafka），降低运维复杂度，利用已有 git 仓库做持久化和回滚。

2. **共享仓库 + 本地记忆双重保存** — 每条经验既写入 Agent 自身的本地记忆系统，也写入跨 Agent 共享仓库，兼顾个人快捷检索和团队级复用。

3. **中文优先 + 精简记录** — 每条知识一条记录，不写流水账；中文记录降低所有 Agent（特别是中文优化的模型）的理解门槛。

4. **版本控制统一管理** — 所有共享文件和消息通过 `git` 管理，提供变更历史追溯和回滚能力，消除"某 Agent 误删/误改"的风险。

5. **异构 Agent 联邦** — 不要求所有 Agent 使用同一模型或同一运行时环境（WSL vs Windows），通过文件协议解耦。Hermes 作为主调度节点承担消息网关职责。

6. **资产目录双规范** — 新脚本/工具必须放 `catalog/scripts/` 或 `catalog/skills/`，确保 web 界面可检索，而不是散落在各处。

7. **禁止 C 盘存储** — 所有文件/脚本/记录禁止放系统盘，防止系统盘空间不足或权限问题影响 Agent 运行。

8. **发现即写入 + 看到错误直接修复** — 不等待用户指示，Agent 有自主维护共享知识的义务，保持知识的时效性和准确性。

## 优化方向

1. **消息队列升级方向** — 当前基于文件轮询的消息机制存在延迟，可考虑引入轻量级文件变更监听（如 `inotifywait` / `ReadDirectoryChanges`）实现实时消息推送，消除轮询等待。

2. **Agent 角色自动发现** — 当前 Agent 清单手动维护在 `cross-agent-rules.md` 中，可扩展为 Agent 启动时自动注册（在共享仓库写入一条存活记录 + 心跳），实现动态发现和健康检查。

3. **消息格式标准化** — 当前消息为自由格式 .md 文件，可定义结构化元数据头（YAML front matter：from/to/type/priority/expires），支持优先级排序、超时清理、自动归档。

4. **知识去重与自动摘要** — 随着共享仓库增长，可能产生重复或过时条目，可引入自动去重脚本 + 定期摘要生成（如每月知识图谱）。

5. **文件锁/冲突避免** — 多个 Agent 同时写入共享仓库可能产生 git 冲突，可引入 `LOCK` 文件机制或约定写前 `git pull`、写后 `git push` 的原子操作规范。

6. **Agent 间异步回调模式** — 当前 Hermes 回复写回文件后，请求方 Agent 需主动轮询，可增加回调标记机制（如请求方在消息中指定 wake 信号），减少无效轮询。

7. **启动阶段优化** — 所有 Agent 启动时都 git pull 可能产生冗余网络请求，可引入共享仓库的本地文件变更时间戳缓存，仅在有变更时拉取。

```
