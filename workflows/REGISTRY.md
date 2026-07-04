# Workflow Registry

> **单一权威触发注册表** — 一个触发词 → 一个工作流，没有歧义。
> 启动/收到指令时，先查本表匹配触发词，再读对应工作流详情。

---

## 快速映射表

### 📝 内容生产

| 触发词（用户说话） | → 工作流 | 优先级 | 详情 |
|------|------|--------|------|
| **发文/开始运营/今天发什么/写文章** | → **W01: Content Orchestrator（三AI全流程）** | **P0** | 豆包→Gemini→DeepSeek→审核→发布 |
| 三AI协作/精耕细作/深度写/好好写 | → W01: Content Orchestrator | P0 | 同上，同一条管线 |
| **快速发文/一键发文/紧急发文/发一篇** | → **W02: Quick Publish（单AI→公众号）** | **P1** | DeepSeek→起草→推送 |
| 多平台发布/分发/发多个平台 | → W03: Multi-Platform Publish | P1 | publish.py |
| 融合文章/借壳生蛋/选题枯竭 | → W04: Content Fusion | P1 | 四种创作模式 |
| 写世界一隅/哲思文章 | → W01 --track thinking | P0 | 内容线的变体 |

### 🎬 视频生产

| 触发词 | → 工作流 | 优先级 | 详情 |
|------|------|--------|------|
| 生成视频/做视频/视频管线 | → W05: Video Pipeline | P1 | Remotion 6步 |
| 视频封面/素材生成 | → W05: Video Pipeline | P1 | 同上 |
| 发布视频/传视频 | → W05: Video Pipeline | P1 | 含自动上传 |

### 🔧 运营工具

| 触发词 | → 工作流 | 优先级 | 详情 |
|------|------|--------|------|
| 审计/五件套/跑审计 | → W06: Audit Suite | P0 | 五步审计 |
| 发邮件/写邮件/发信 | → W07: Email Send | P1 | SMTP |
| 知乎回答/自动答 | → W08: Zhihu Answer | P1 | 自动搜→答 |
| 闲鱼发货/商品发货 | → W09: Goofish Delivery | P1 | 自动发链接 |
| 仪表盘/发布状态 | → W10: Content Dashboard | P1 | Web仪表盘 |
| 谜题匹配/推理解谜 | → W11: Reasoning Match | P2 | 文章→谜题 |

### 📋 收尾

| 触发词 | → 工作流 | 优先级 | 详情 |
|------|------|--------|------|
| 项目做完/收尾/清理 | → W12: Project Close | P0 | 审计→存→发文 |
| 存经验/存记忆 | → W13: Memory Save | P0 | 写记忆+push |

### 🏗️ 外部系统（非内容管线）

| 触发词 | → 工作流 | 优先级 | 详情 |
|------|------|--------|------|
| CAD/FreeCAD/AutoCAD | TextToCAD | P0 | NL→CAD |
| Reasonix/多智能体 | Reasonix | P0 | AI团队编排 |
| 变现/赚钱/付费 | Content Monetization | P1 | 四层漏斗 |
| 踩坑/错误记忆 | Pitfall Recorder | P0 | 自动记忆 |

---

## 优先级规则

1. **P0 同时匹配多个** → 问用户走哪个（"你是想深度写（三AI）还是快速发一篇？"）
2. **P0 + P1 同时匹配** → 走 P0（三AI全流程优先于单AI快速发）
3. **同优先级多个匹配** → 问用户确认
4. **收到"发文"但最近刚深度写过** → 默认走 W02 Quick Publish

---

## 工作流详情

### W01: Content Orchestrator（三AI协作全流程）

- **状态**: ✅ 生产运行 · 核心管线
- **入口脚本**: `~/catalog/scripts/content_orchestrator.py`
- **技能**: `content-orchestrator`（触发词已排他）
- **架构文档**: `~/architectures/systems/content-orchestrator/README.md`

#### 触发词（唯一归属）

**发文、开始运营、今天发什么、写文章、三AI协作、精耕细作、深度写、出文章、好好写**

> ⚠️ 以上触发词**不**属于其他任何技能。

#### 步骤

```
Step 0: 参数解析 → topic + track(ai/thinking) + mode(full/skeleton/draft/refine)
Step 1: 选题调研 → 豆包/Gemini/DeepSeek 自动降级搜索（热点+角度）
  ↓ 👀 审核闸门（继续/修改/重做/跳过）
Step 2: 骨架生成 → 豆包/Gemini/DeepSeek 自动降级（文章结构+初稿）
  ↓ 👀 审核闸门
Step 3: 精加工 → 豆包/Gemini/DeepSeek 自动降级（文献补充+修正）
  ↓ 👀 审核闸门
Step 4: 文章组装 → 清洗+合并+写入文件（含YAML frontmatter）
  ↓ 👀 发布前终审
Step 5: 公众号发布 → publish_one.py（封面生成+推送草稿）
Step 6: 视频生成 → video_pipeline.py（可选）
Step 7: 内容登记 → content_dashboard.py
```

#### 两条内容线

| 参数 | 品牌 | 定位 | 豆包搜索Prompt | Gemini骨架Prompt |
|------|------|------|------|------|
| `--track ai` | 美好需要创造 | AI提效实战派——讲人话、给干货、可实操 | "你是公众号「美好需要创造」的AI主编。定位：AI提效实战派——讲人话、给干货、可实操。搜索以下话题的最新动态、实用技巧、反常识观点：" | "请以「AI提效实战派」的风格写一篇公众号文章。要求：说人话、给干货、可实操。开头抓人、中间有案例、结尾有行动指南。标题<=9字，摘要<=17字。标注金句（用于视频脚本）。" |
| `--track thinking` | 美好需要创造 / 世界一隅 | 反共识、有深度、可传播——不写鸡汤，写刺痛 | "你是专栏「世界一隅」的主笔。定位：反共识、有深度、可传播——不写鸡汤，写刺痛。搜索以下话题的争议性观点、最新讨论、经典文献：" | "请以「世界一隅·哲思」的风格写一篇深度文章。要求：反共识但不反智，有故事感，不做学术腔。开头有钩子，中间有推进，结尾有余韵。标题<=9字，摘要<=17字。标注金句（用于视频脚本）。品牌色参考：深海蓝 #1a1a2e + 暖金 #c8a03c" |

#### 自动降级链

```
豆包(doubao_search.py) → 失败 → Gemini(gemini_search.py) → 失败 → DeepSeek(deepseek_search.py) → 全部失败 → 提示稍后重试
```

#### 审核闸门

每步之间展示内容，提供5个选择：
```
[Enter] 继续
[m] + 修改意见 → 追加到prompt重跑
[r] 重新生成
[s] 跳过这一步
[q] 终止整个流程
```

#### 命令行示例

```powershell
cd ~/catalog/scripts
python content_orchestrator.py "Cursor技巧" --full --track ai          # 全流程AI提效线
python content_orchestrator.py "人生算法" --full --track thinking       # 全流程哲思线
python content_orchestrator.py "话题" --full --fast --track ai          # 快速(跳过审核)
python content_orchestrator.py "话题" --skeleton                        # 只看骨架
python content_orchestrator.py "文章.md" --refine                       # 精加工已有文章
```

---

### W02: Quick Publish（单AI→公众号快速发布）

- **状态**: ✅ 生产运行 · 快速通道
- **入口脚本**: `~/world-corner-blog/scripts/publish_one.py`
- **技能**: `wechat-publish`（触发词已排他）
- **架构文档**: `~/architectures/systems/publishing-pipeline/README.md`

#### 触发词（唯一归属）

**快速发文、一键发文、紧急发文、发一篇、推一篇、快速发**

> ⚠️ **不**包含"发文""开始运营""写文章"——这些属于 W01。

#### 步骤

```
[0/5] AI选题 → 自动搜索今日热点，推荐3个选题（如果是手动指定话题则跳过）
[1/5] DeepSeek搜索 → 搜话题的最新观点+数据+案例，寻找逻辑矛盾
[2/5] JSON起草 → 生成 {title, digest, body} 三字段JSON
       支持 --推理 模式：结构=迷面→解谜→答案
       不指定模式的默认结构=壹贰叁章节
[3/5] 公众号推送 → 封面生成→上传素材→创建草稿
[4/5] 内容登记 → RegistryManager 写入发布记录
```

#### 起草 Prompt（嵌入 publish_one.py）

**常规模式（无 --推理）：**
```
你是公众号作者「美好需要创造」。定位：AI提效实战派。
选题：「{topic}」。
参考资料：{intel[:600]}

直接输出一个JSON（不要```标记）：
{{"title":"标题<=9字","digest":"摘要<=17字","body":"## 壹 · 标题\n正文\n✦ 金句\n\n## 贰 · 标题\n正文\n✦ 金句\n\n## 叁 · 标题\n正文\n✦ 金句\n\n关注公众号「美好需要创造」，闲鱼搜「AI编程踩坑清单」"}}

body中用##壹贰叁做章节，每章配✦金句独占一行。语调接地气，不教学不说教。
```

**推理模式（--推理 / --logic）：**
```
一样，但 body 结构用：
## 壹 · 迷面 → 抛矛盾现象
## 贰 · 解谜 → 一步步推理排除干扰项
## 叁 · 答案 → 结论+判断框架

style_extra = "文章结构采用「抛矛盾→推理解谜→给答案」的逻辑推理框架。开头像一道逻辑题（\"这里有三个看似矛盾的事实…\"），正文是解题过程，结尾像答案揭晓。保持推理感和悬念感。"
```

#### 命令行示例

```powershell
cd ~/world-corner-blog/scripts
python publish_one.py                          # AI自动选题+发布
python publish_one.py "Cursor技巧"              # 指定选题
python publish_one.py "生态位法则" --推理         # 推理模式
```

---

### W03: Multi-Platform Publish（多平台分发）

- **状态**: ✅ 生产运行
- **入口脚本**: `~/catalog/scripts/publish.py`
- **技能**: 无独立技能（通过内容管线触发）

#### 触发词（唯一归属）

**多平台发布、分发、发多个平台、全平台发布、同步到各平台**

#### 支持平台

| 平台 | 命令参数 | 接口方式 |
|------|----------|----------|
| 公众号 | `--wx-only` | REST API |
| 知乎 | `--zhihu` | Playwright |
| 掘金 | `--jj-only` | API + Cookie |
| B站专栏 | `--bilibili` | API + Cookie |
| 腾讯云社区 | `--tencent` | Playwright |
| 即刻 | `--jike` | Playwright |

#### 命令行示例

```bash
python publish.py article.md --zhihu --juejin --jike
python publish.py article.md --wx-only                          # 仅公众号
python publish.py article.md --tencent --afdian                 # 腾讯云+爱发电
```

---

### W04: Content Fusion（借壳生蛋）

- **状态**: ✅ 可用
- **架构文档**: `~/architectures/patterns/content-fusion-framework.md`

#### 触发词（唯一归属）

**融合文章、借壳生蛋、选题枯竭、没选题、不知道写什么、融合框架**

#### 四种创作模式

| 模式 | 公式 | 适用场景 |
|------|------|----------|
| A | 热点→哲学 | 社会热点→提炼底层规律 |
| B | 技术→人文 | 新技术→对普通人的影响 |
| C | 思想人物→技术 | 哲学家/作家思想→解读AI时代 |
| D | 跨界碰撞 | 两个不相关的领域→新洞察 |

#### 步骤

```
Step 1: 找冷门好内容（红迪/知乎/学术论文/经典书籍）
Step 2: 用四种模式之一替换上下文
Step 3: 注入品牌风格（深海蓝+暖金）
Step 4: 发布
```

---

### W05: Video Pipeline（视频生成管线）

- **状态**: ✅ 生产运行 · V1
- **入口脚本**: `~/projects/remotion-video-platform/scripts/video_pipeline.py`
- **技能**: `video-pipeline`
- **架构文档**: `~/architectures/systems/video-pipeline/README.md`

#### 触发词（唯一归属）

**生成视频、做视频、视频管线、视频制作、remotion、素材生成、视频封面、发布视频**

#### 6步管线

```
Step 1: hook → suggest_hook.py 分析文章匹配最优钩子(8种公式)
Step 2: articles → 文章内容处理/卡片组装
Step 3: assets → generate_assets.py 生成封面+背景（10套主题）
Step 4: tts → TTS语音+BGM合成，钩子感知调整语气
Step 5: render → Remotion渲染视频（1080×1920 竖屏）
Step 6: registry → 元数据写入注册表
```

---

### W06: Audit Suite（审计五件套）

- **状态**: ✅ 生产运行
- **技能**: `audit`
- **架构文档**: `~/claude-memory/global/workflows/audit-four-piece.md`

#### 触发词（唯一归属）

**审计、审计一下、跑审计、五件套、代码审计、质量检查、检查项目、方向一审计**

#### 五步审计

```
① 规则脚本审计 → 方向一默认只跑这个
② LangGraph审计
③ 代码审查
④ CrewAI审计
⑤ 统计审计
```

---

### W07: Email Send（发邮件）

- **状态**: ✅ 生产运行
- **技能**: `send-email`
- **脚本**: `~/catalog/scripts/gmail_v3.py`

#### 触发词（唯一归属）

**发邮件、写邮件、发信、邮件通知、发给xxx、email**

---

### W08: Zhihu Answer（知乎自动答）

- **状态**: ✅ 生产运行
- **脚本**: `~/world-corner-blog/scripts/zhihu_answer.py`

#### 触发词（唯一归属）

**知乎回答、自动答、知乎问题、答知乎**

---

### W09: Goofish Delivery（闲鱼发货）

- **状态**: ✅ 生产运行
- **脚本**: `~/catalog/scripts/goofish_delivery.py`

#### 触发词（唯一归属）

**闲鱼发货、商品发货、发货、自动发货、闲鱼**

---

### W10: Content Dashboard（仪表盘）

- **状态**: ✅ 生产运行
- **脚本**: `~/catalog/scripts/content_dashboard.py`

#### 触发词（唯一归属）

**仪表盘、发布状态、查看发布、统计、内容统计**

---

### W11: Reasoning Match（谜题匹配）

- **状态**: 🔧 开发中
- **脚本**: `~/world-corner-blog/scripts/logic_matcher.py`
- **架构文档**: `~/architectures/systems/reasoning-library/README.md`

#### 触发词（唯一归属）

**谜题匹配、推理解谜、找谜题、推理素材、逻辑谜题**

---

### W12: Project Close（收尾三件套）

#### 触发词（唯一归属）

**收尾、项目做完、做完了、清理、完结**

#### 标准流程

```
① 审计五件套 → 方向一规则脚本审计
② 存入经验 → 踩坑/新技能/工具用法写进 claude-memory/，commit+push
③ 写成文章 → 提炼原则→品牌风格→公众号草稿+世界一隅博客
```

---

### W13: Memory Save（存经验）

#### 触发词（唯一归属）

**存经验、存记忆、记一下、记住了、这个要记住、保存到记忆**

#### 流程

```
1. 判断是否已有相似记忆 → 有则升级，不新建碎片
2. 写入 ~/claude-memory/ 对应目录
3. 更新 TRIGGERS.md（新场景→新路由条目）
4. git add + commit + push
```

---

## 已废弃/被取代的工作流

| 旧工作流 | 被谁取代 | 废弃原因 |
|----------|----------|----------|
| Unified Operations Pipeline V4 | content-orchestrator + publish_one.py | DAG编排太重，拆为轻量脚本 |
| yuanbao_pipeline.py | content-orchestrator | 元宝废弃，换三AI引擎链 |
| Publishing Pipeline V7 | content-orchestrator | 整合进三AI流程 |
| Publishing Pipeline V8 | content-orchestrator + V9 | V9独立平台适配 |
| pipeline_dag.py | publish_one.py | 简化为一站式脚本 |

---

## 全工作流总览图

```
                             触发词
                                │
                    ┌───────────┴───────────┐
                    │       REGISTRY.md      │ ← 先查本表
                    └───────────┬───────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ 内容生产管线  │   │  视频管线     │   │  运营工具        │
    │              │   │              │   │                  │
    │ W01 三AI全流  │   │ W05 视频管线  │   │ W06 审计五件套   │
    │ W02 快速发布  │   │              │   │ W07 邮件         │
    │ W03 多平台    │   │              │   │ W08 知乎         │
    │ W04 融合      │   │              │   │ W09 闲鱼发货     │
    │ W11 谜题匹配  │   │              │   │ W10 仪表盘       │
    └──────────────┘   └──────────────┘   └──────────────────┘
```

---

## 响应规则

### 当我说了触发词后，你按以下顺序执行：

1. **查本注册表** — 找到对应 W0X 工作流
2. **读工作流详情** — 读对应文件或系统 README
3. **如果 P0 级多个匹配** — 问用户："你是想深度写（三AI全流程）还是快速发一篇？"
4. **执行工作流** — 按步骤描述操作
5. **如果卡住** — 回到第 1 步，重新查注册表确认方向
6. **如果连续两次猜错方向** — 列出所有匹配的 P0 工作流让用户选

---

## 参见

- [INDEX.md](../INDEX.md) — 架构总索引
- [systems/content-orchestrator/README.md](../systems/content-orchestrator/README.md) — 三AI系统架构
- [systems/publishing-pipeline/README.md](../systems/publishing-pipeline/README.md) — 发布管线架构
- [patterns/multi-agent-orchestration.md](../patterns/multi-agent-orchestration.md) — 多智能体模式
- `~/claude-memory/TRIGGERS.md` — 启动时触发表（已指向本注册表）
