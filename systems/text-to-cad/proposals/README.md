# TextToCAD Eval 评测体系 (V2) 架构

> 提供 Eval-driven Development 评测基础设施，确保 TextToCAD 项目中每次系统提示词修改都能通过自动化测试验证，防止回归退化。核心信条：**准确率 < 90% 不发**。任何修改必须经过「修提示词 → 跑相关用例 → 跑全量 → 对比报告」四步流水线，通过后方可发布。

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                  t2cad_eval.py (CLI)                │
│                                                     │
│  init  ──→  run  ──→  compare  ──→  report  migrate │
└────────┬────────────────────────────────────────────┘
         │ --project --tool --suite --tag --dry
         ▼
┌─────────────────────────────────────────────────────┐
│                  Dataset Loader                      │
│                                                     │
│  gold_set/  edge_cases/  regression/                │
│  ┌──────┐    ┌──────┐     ┌──────┐                 │
│  │excel │    │excel │     │excel │  ← per tool      │
│  │cases │    │cases │     │cases │                 │
│  │.json │    │.json │     │.json │                 │
│  └──────┘    └──────┘     └──────┘                 │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│               Scoring Pipeline                      │
│                                                     │
│  Code Gen  →  Syntax(20%)  →  Safety(30%)           │
│  (LLM)           │              │                    │
│                  ▼              ▼                    │
│             ast.parse()    Pattern Match             │
│                  │              │                    │
│                  ▼              ▼                    │
│           TaskMatch(30%)  →  CodeQuality(20%)       │
│           must_use/match    comments/func/naming    │
│                                                     │
│  Aggregate: weighted sum >= 90% → PASS              │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Results Store (JSON)                   │
│  eval/results/{project}_{tool}_{timestamp}.json     │
│                                                     │
│  compare: load 2 snapshots → diff matrix            │
│  report:  aggregate last N days → trend markdown    │
└─────────────────────────────────────────────────────┘

         Prompt Iteration Workflow:
         ┌──────────┐
         │ Found Bug│
         └────┬─────┘
              │
         ┌────▼──────────────┐
         │ Fix system prompt │
         └────┬──────────────┘
              │
         ┌────▼──────────────────┐
         │ run --tag <tag>       │  ← 筛选相关用例
         │   ALL PASS?           │
         └────┬──────────┬───────┘
              │ YES      │ NO ──→ back to fix
         ┌────▼──────────┘
         │ run (full)            │  ← 全量回归
         │   PASS RATE >= 90%?   │
         └────┬──────────┬───────┘
              │ YES      │ NO ──→ revert, redesign
         ┌────▼──────────┘
         │ compare before/after  │  ← 确认无退化
         │ diff positive?        │
         └──────────────────────┘
              │
         ┌────▼──────┐
         │   Release │
         └───────────┘
```
```

## 核心组件

## 目录结构（`~/.text_to_cad/`）

| 组件 | 路径 | 职责 |
|------|------|------|
| **评测引擎** | `t2cad_eval.py` | CLI 入口，V2 项目级调度器，支持 init/run/compare/report/migrate |
| **黄金集** | `eval/datasets/<project>/gold_set/` | 必过集合，每个用例必须 100% 通过 |
| **边界集** | `eval/datasets/<project>/edge_cases/` | 鲁棒性测试，空数据/特殊字符/极端值 |
| **回归集** | `eval/datasets/<project>/regression/` | 历史缺陷回归，防止已修复 bug 重现 |
| **结果仓库** | `eval/results/` | 时间戳命名的 JSON 快照，支撑 compare 历史对比 |

## 评分四维

| 维度 | 权重 | 验证方式 |
|------|:--:|---------|
| 语法 | 20% | `ast.parse()` 检查 |
| 安全 | 30% | 禁止模式匹配（import/Dispatch/open/print/exit/subprocess/eval） |
| 任务匹配 | 30% | 函数包含检查 + 期望操作命中 + 禁止函数排除 |
| 代码质量 | 20% | 注释/函数封装/变量命名/异常处理 |

综合 >= 90% 为通过。

## 测试用例模型

每个用例包含：name, description, snapshot（数据快照）, user_input, checks（must_use/must_not_use/expected_operations/should_contain）, difficulty（easy/medium/hard）, tags。

checks 定义约束：must_use 缺失扣 15% 每项, must_not_use 出现扣 20% 每项, expected_operations 全不中扣 20%, should_contain 为加分项。

## 工具隔离

按 project + tool 两层命名空间隔离，一个项目多个工具可独立评测（如 t2cad+excel, t2cad+cad, sql-gen+excel）。

## 数据流

1. **初始化** → `init --project <p> --tool <t>` 创建目录骨架和空用例集
2. **输入** → CLI 接收 --project, --tool, --suite, --tag, --dry 等参数，读取对应目录的 JSON 用例文件
3. **执行** → 评测引擎遍历匹配的用例，对每个用例执行 LLM 调用（生成代码）→ 输出代码 → 评分四维打分（语法→安全→任务匹配→代码质量）→ 聚合加权分
4. **存储** → 结果写入 `eval/results/{project}_{tool}_{timestamp}.json`（历史归档）
5. **对比** → `compare` 命令加载两次历史结果，输出差异矩阵（各维度涨跌/总通过率变化）
6. **报告** → `report --last 7days` 聚合周趋势，输出 markdown 格式

## 提示词迭代工作流

发现 bug → 修系统提示词 → `--tag` 筛选跑相关用例 → PASS → 全量跑（回归检查） → `compare` 对比差异 → 通过则发布，不通过则撤销

## 关键设计决策

1. **项目级隔离（V2 关键升级）** — 按 `<project>/<tool>` 分层存放用例，支持多项目复用同一引擎（t2cad + sql-gen 等），而非单目录平铺
2. **黄金集 + 回归集双轨** — 黄金集保证能力基线不动摇，回归集专门捕获已修复缺陷，防止「改 A 修 B 却坏了 C」的回退陷阱
3. **评分权重偏安全（30%）** — 对于代码生成场景，安全比功能更重要（禁止 import/Dispatch/eval/subprocess 等危险操作），这个权重设计体现了「宁可少做，不可乱做」的原则
4. **90% 硬阈值** — 不设 100% 给合理容错空间（代码风格差异），但 90% 以上才发确保核心质量
5. **用例设计最小化原则** — 每个工具最少 5 个用例（基础 1-2 + 多步组合 1-2 + 边界 1 + 复杂 1），以低成本覆盖大部分高风险路径，避免用例膨胀导致评测耗时过长
6. **多粒度筛选** — --suite（集合级别）、--tag（功能标签）、--dry（干跑）三种筛选维度，支持从调试到全量的渐进式运行
7. **迁移路径** — `migrate` 子命令提供 V1→V2 平滑迁移，不破坏已有用例

## 优化方向

## 隐含和可探索的优化方向

1. **自动用例生成** — 当前用例手动编写，可引入 LLM 根据历史失败自动生成回归用例，降低维护成本
2. **并行评测** — 多个用例可并发执行，当前似串行；引入线程池/异步可大幅缩短全量评测时间
3. **CI/CD 集成** — 当前 CLI 手动触发，可接入 Git hooks（pre-commit/pre-push），自动阻截退化提交
4. **评测缓存** — 同一提示词 + 同一用例的结果可缓存，减少重复 LLM 调用（当前每次 run 都重新生成）
5. **用例质量度量** — 没有兜底机制衡量「用例本身的好坏」；可引入 mutation testing 测用例是否真正捕捉缺陷
6. **权重动态调优** — 四维权重当前硬编码；可基于历史数据（某维度频繁拖累通过率）自动校准权重
7. **报告增强** — 周报当前只输出 markdown；可扩展为 HTML 看板（趋势图/雷达图/详情 drill-down）

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/global/tools/t2cad-eval-system.md`*
