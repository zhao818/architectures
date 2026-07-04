# 工程资料智能平台 v0.2.0 — 架构概要 架构

> **工程资料智能平台** 是一个面向工程资料全生命周期管理的自动化系统，核心目标是将检验批填写、审核、归档等繁重、重复、易出错的工程资料工作从人工转为智能自动化。系统以 **项目为中心** 而非以 Agent 为中心——所有功能入口都是工程项目，系统根据项目类型自动推荐工作流、调用 Agent、应用规则，最终输出符合规范的工程文档。当前阶段聚焦于 **检验批自动填写（Fill Agent）**，远期覆盖施工日志、报验单、审核、归档、BIM 集成等全链路。

## 架构概览

```
                    ┌─────────────────────────────────────────────────┐
                    │                 PROJECT CENTER (L1)             │
                    │  项目全生命周期 — 一切围绕项目工作               │
                    │  Project → Bid → Unit → Divisional → Item → Lot │
                    └───────────────────────┬─────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │               WORKFLOW CENTER (L3)              │
                    │  流程自动化编排 — 最重要的中间层                 │
                    │  状态机: PENDING→RUNNING→WAITING→COMPLETED/FAIL │
                    └────┬───────────┬────────────┬───────────────────┘
                         │           │            │
               ┌─────────┘    ┌──────┘     ┌─────┘
               ▼               ▼            ▼
     ┌─────────────────┐ ┌──────────┐ ┌──────────────────────┐
     │  AGENT CENTER   │ │  RULE    │ │     AI CENTER        │
     │  (L2)           │ │  ENGINE  │ │     (L7)             │
     │  Fill/Review/   │ │  (+1层)  │ │  Planner / LLM /     │
     │  Project/Doc/   │ │  ────────│ │  RAG / Memory /       │
     │  Archive/QA     │◄│►7类规则 ◄│►│  Prompt / ToolCall / │
     │  Agent          │ │  ERROR   │ │  Evaluation /         │
     └────────┬────────┘ │  WARNING │ │  Reflection           │
              │          │  INFO    │ └──────────┬─────────────┘
              │          └────┬─────┘            │
              │               │                  │
              └───────┬───────┴──────┬───────────┘
                      │              │
              ┌───────▼──────────────▼───────────┐
              │        DOCUMENT ENGINE (L5)       │
              │  统一文档抽象 — 外部不看格式       │
              │  create/read/update/convert/sign  │
              └────────────────┬─────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │          TOOL CENTER (L8)         │
              │  原子能力: Word/Excel/PDF/CAD/OCR │
              │  /企业微信/电子签章/工程计算       │
              └────────────────┬─────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │           DATA CENTER (L6)        │
              │  SQLite + FS + sqlite-vec         │
              │  Project/Document/Workflow/       │
              │  Knowledge/System 5层数据          │
              │  版本管理 + 审计日志               │
              └──────────────────────────────────┘
```

### AI-Rule-Tool 协作循环（核心模式）

```
  AI Center 生成内容
      │
      ▼
  Rule Engine 逐规则校验（编号→格式→引用→日期→完整性）
      │
      ├─ ERROR + 可自动修正 → Rule Engine auto_fix() → 重新校验
      ├─ ERROR + 不可修正 → 标记"人工处理"
      ├─ WARNING → 记录审核意见，继续
      └─ 通过 → Document Engine 生成文档 → Data Center 持久化
```

## 核心组件

## 8+1 层架构

系统由 9 个逻辑层组成，严格遵循 **上层调用下层、下层不可调用上层** 的依赖原则，同层之间不互相依赖（通过上层协调）：

| 层级 | 名称 | 职责 | 关键内部结构 |
|------|------|------|-------------|
| L1 | **Project Center** | 工程项目全生命周期管理，系统顶层入口 | Project → BidSection → UnitProject → DivisionalProject → ItemProject → InspectionLot 六级层级；项目类型（水利/市政/建筑/公路/桥梁）；状态机（筹建→在建→竣工→归档） |
| L2 | **Agent Center** | 可无限扩展的专业 Agent 集合，每个 Agent 是一个领域能力单元 | Fill Agent（自动填写）、Review Agent（审核）、Project Agent（项目理解）、Document Agent（资料管理）、Archive Agent（归档）、QA Agent（质量检查）；远期 Risk/Schedule/Material/Bridge/BIM Agent。Agent 间不直接调用，通过 Workflow Center 编排。无状态设计 |
| L3 | **Workflow Center** | **最重要的中间层** — 流程自动化编排，非按钮驱动 | 定义 Workflow（有序步骤）和 WorkflowStep（6 种类型：AGENT/RULE/TOOL/HUMAN/GATE/PARALLEL）；状态机 PENDING→RUNNING→WAITING_HUMAN→RUNNING→COMPLETED/FAILED/REJECTED；步骤支持 input/output mapping、超时、重试、fallback。当前已实现 fill_document（4步4.4s）和 audit_wage 两个 Workflow |
| L4 | **Knowledge Center** | 所有工程知识的中心化存储与检索 | 5 大知识分类：国家规范、地方规范、企业标准、标准图集、历史项目经验；混合检索（向量语义 + 结构化 SQL + 关键词 + 文件系统索引）；接口：search()、get_specification()、get_template_guide() |
| L5 | **Document Engine** | **核心层** — 统一文档引擎，上层不需要知道文档是什么格式 | 统一 Document 抽象（id/project_id/version/status/metadata/content）；接口：read/create/update/convert/export/sign；模板系统（DocumentTemplate + TemplateField 定义可填字段和数据来源）；支持 Word/Excel/PDF/CAD/图片/扫描件/电子签章/HTML/Markdown |
| L6 | **Data Center** | 数据持久化与版本管理 | 5 层数据分层（Project/Document/Workflow/Knowledge/System Data）；当前 SQLite（结构化）+ 文件系统（大文件）+ sqlite-vec（向量）；版本管理（DocumentVersion 快照+diff+回滚）；权限模型（admin/engineer/viewer/auditor）；接口：DataService 统一访问层 |
| L7 | **AI Center** | AI 模型管理层，非 Agent 层 | 8 个子模块：Planner（任务规划）、LLM（模型路由/切换/降级）、RAG（知识检索策略）、Memory（记忆管理）、Prompt（模板版本化）、Tool Calling（AI→Tool 调用控制）、Evaluation（质量评估）、Reflection（自我修正）。接口：AIService.execute(task, model, tools, rules)。模型路由按任务复杂度分层（Qwen/GPT-4o-mini 低→DeepSeek/Claude Haiku 中→Claude Sonnet/Opus 高） |
| L8 | **Tool Center** | 原子能力层，AI 决定调用时机，Tool 负责执行 | 6 大类工具：Document Tools（Word/Excel/PDF/模板填充）、Parse Tools（docx/dwg/dxf/image/OCR）、CAD Tools（reader/extractor）、Communication Tools（企业微信/邮件/打印）、Data Tools（报表/图表/导出）、Misc Tools（签章/天气/计算器）。统一接口规范：Tool(name, description, parameters) + execute(params) → ToolResult(success, data, error, duration_ms) |
| +1 | **Rule Engine** | **用户追加层** — 确定性规则执行，不依赖 AI | 7 类规则：编号（编号格式+流水号）、日期逻辑（工序时间约束）、完整性（字段组合必填）、格式（单位/日期/精度统一）、引用（规范版本有效性）、资料成套性（竣工资料清单）、工序顺序。三严重级别：ERROR（阻挡性，可自动修正或标记人工）/ WARNING（建议修复）/ INFO（仅供参考）。接口：validate() / auto_fix() / generate()。执行顺序：编号→格式→引用→日期→完整性→成套性 |

### 层间关系

核心关系模式为三层协作的闭环：
- **AI Center** 负责生成内容（智能决策）
- **Rule Engine** 负责校验/修正 AI 输出（确定性保证）
- **Tool Center** 负责执行物理动作（文件操作/消息推送等）

Workflow Center 是唯一的编排者，持有对所有层的调用权。Project Center 是数据上下文的所有者。

## 数据流

## 两条典型数据流

### 1. 检验批填写（核心场景）
```
1. 用户：进入项目 → 选择检验批类型
2. Project Center：返回项目上下文（项目类型/标段/当前进度）
3. Workflow Center：启动"检验批填写"工作流实例
4. Rule Engine：根据编号规则生成检验批编号（确定性）
5. Knowledge Center：检索该检验批引用的规范要求
6. AI Center（Planner→LLM→RAG→Tool Calling）：根据上下文+规范+数据填写内容字段
7. Rule Engine：二次校验 AI 填写内容（编号是否冲突/日期逻辑/量值格式）
8. 校验通过 → Tool Center（Document Tools → Template Filler）：生成 Word 文档
9. Document Engine：添加版本号、电子签章
10. Data Center：存储文档 + 审计日志（谁/何时/做了什么）
11. Project Center：更新检验批状态为"已填"
```

### 2. 日报采集分析（数据驱动场景）
```
1. Tool Center（Communication Tools → WeCom Sender）：扫描企业微信新日报文件
2. Tool Center（Parse Tools → Parser）：提取结构化数据（日期/进度/人员/材料）
3. Data Center：存储原始文件 + 解析结果
4. Workflow Center：自动触发"日报分析"工作流
5. AI Center：汇总多日报数据，生成分析总结
6. Rule Engine：校验完整性（所有工序是否覆盖）、逻辑一致性（进度是否合理）
7. Tool Center（WeCom Sender）：推送分析总结到企业微信群
8. Data Center：记录推送结果
```

### 数据流核心模式
- **命令流**：用户 → Project Center → Workflow Center → [Agent/AI/Rule/Tool] Center → Data Center
- **反馈流**：Data Center → Project Center（状态更新）→ 用户通知
- **修正循环**：Rule Engine 发现 AI 输出错误 → 自动修正 → 重新校验 → 通过或标记人工
- **规则**：上层调用下层，下层不可反向调用；AI Center 和 Rule Engine 可相互调用（AI 判断何时用规则，规则校验 AI 输出）

## 关键设计决策

## 关键设计决策

| # | 决策 | 选择 | 放弃的方案 | 理由 |
|---|------|------|-----------|------|
| 1 | **架构中心** | 以项目为中心（Project-Centric） | 以 Agent 为中心 | 工程领域实际流程是围绕项目展开的，用户关注"资料走完没有"而非"什么 Agent 在工作"，更贴合真实业务 |
| 2 | **分层原则** | 严格单向依赖，上层调用下层 | 扁平调用、任意依赖 | 保证每层可独立替换（AI 换、工具换、数据库换不影响业务逻辑），避免循环依赖导致的架构腐化 |
| 3 | **Rule Engine vs AI** | 确定性规则独立为层，优先级高于 AI | 全部交给 AI 或全部硬编码 | 工程资料不是作文——编号格式、日期逻辑、规范引用必须确定、可验证。AI 做判断、规则做校验，各司其职 |
| 4 | **Workflow Center 独立性** | 独立中间层，专职编排 | 把流程逻辑分散在各 Agent 中 | "流程"本身是工程资料的核心概念，需要有状态、可追踪、可审计。大多数 AI 项目缺失这一层导致难以落地 |
| 5 | **Agent 无状态** | Agent 不存储状态 | Agent 自带状态 | 状态统一在 Workflow Center（流程状态）和 Project Center（业务状态），Agent 可热替换、可横向扩展 |
| 6 | **AI Center ≠ Agent Center** | AI Center 管模型技术，Agent Center 管业务能力 | 合并为一层 | 明确分工：Agent 定义"做什么"，AI Center 定义"用什么模型、什么策略做"。换模型不改 Agent 逻辑 |
| 7 | **模板 vs 文档分离** | Document Engine 有独立的模板系统 | 模板和文档混在一起 | 模板（Template）可复用、可版本化，不同的字段可以标注数据来源（rule/ai/human/extract），支持增量填充 |
| 8 | **首次交付降级** | Fill Agent 跳过 Workflow/KR Center，直接调用 | 一步到位全架构 | 先跑通最小闭环：Rule Engine 生成编号 → Tool Center 填充模板 → AI Center 填写 → Rule Engine 校验 → Data Center 保存。Workflow 和 Knowledge 之后接入 |
| 9 | **模型路由按任务分层** | 不同复杂度走不同模型 | 全部用最强模型或全部用便宜模型 | 简单填表用 Qwen/GPT-4o-mini（低成本），精细审核用 Claude Sonnet/Opus（高质量），确定性任务走 Rule Engine（零成本） |
| 10 | **数据存储混合策略** | SQLite + 文件系统 + sqlite-vec | PostgreSQL（过早引入） | 开发阶段保持轻量，后期按需 PostgreSQL 迁移。大文件不走数据库，规则定义用 JSON/YAML 保持人工可编辑 |

### 架构哲学总结
**分层可替换** — 每一层都可以独立更换实现而不影响业务逻辑。Rule Engine 是用户专门追加的一层，因为工程资料的"确定性"比 AI 的"智能"更重要。同层不互相依赖，通过 Workflow Center 编排，避免 Agent 直接调用工具等违反分层原则的模式。

## 优化方向

## 优化方向（来自文档中的"将来可能包含"清单 + 架构推断）

### 近期高优先级
- **Knowledge Center 接入 Fill Agent** — 当前硬编码规范，需要接入 Knowledge Center 的 RAG 检索实现规范自动匹配
- **Workflow Center 编排 Fill Agent** — 当前直接调用，需要接入 Workflow Center 实现完整的流程状态追踪和人工复核节点
- **Rule 扩增至 12+ 条** — 从当前 6 类基础规则扩充到覆盖更多工程场景

### 中期优化方向
- **工具执行成本感知路由** — AI Center 调用 Tool Center 前评估调用成本（API 费用、执行时间），自动降级到低成本方案
- **Prompt 自动优化** — 根据 Evaluation 模块的历史评分为每个 PromptTemplate 自动调优
- **多模型 A/B 对比** — 同一任务用不同模型执行，输出对比，选择最优
- **AI 输出缓存** — Cache 相同输入（相同项目+相同模板+相同规范），节省 API 费用
- **模型降级链** — ModelConfig 支持 `fallback: List[ModelConfig]`，主模型不可用时自动降级
- **文档版本对比** — 高亮显示不同版本的差异，方便审核人员快速定位变更
- **工作流可视化编辑器** — 拖拽编排 Workflow，让非技术用户自定义审批流程

### 远期优化方向
- **PostgreSQL 迁移** — SQLite → PostgreSQL，支持高并发和多用户
- **监控/日志/费用统计** — LLM 调用成本监控与预算控制，执行效率分析
- **多用户/权限系统** — admin/engineer/viewer/auditor 角色 + 操作级权限
- **Web 界面** — 从 CLI 升级为 Web 应用，支持浏览器操作
- **规则热加载** — 修改规则文件无需重启系统
- **规则测试沙箱** — 安全测试新规则是否生效
- **工作流执行历史回溯与重放** — 调试和审计用
- **Revit/BIM 集成** — 自动提取 BIM 模型数据填充资料
- **离线模型支持** — 敏感数据本地推理，不依赖云端 API
- **自动规范更新** — 新规范发布时自动入库，旧规范自动标记废止
- **知识图谱** — 规范间的引用关系图和追溯

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/session/2026-07-04-engineering-doc-platform-v0.2.0.md`*
