# 推理解谜素材库 (reasoning-library) 架构

> 为公众号文章（AI提效实战派+融合框架品牌）在发布后自动匹配最合适的逻辑谜题，自然融入文章内容，增强读者的逻辑参与感和思考深度。核心原则是"后置匹配"而非"前置套模板"——文章完成后根据主题/类型寻找谜题，而非先用谜题框定文章结构。

## 架构概览

```mermaid
flowchart TB
    subgraph 选题阶段
        A[content-orchestrator\nStep 1: AI选题]
        C{矛盾提取}
        D[Step 2: DeepSeek搜索]
        A --> C --> D
    end

    subgraph 写作发布
        E[publish_one.py\nAI起草+推送]
        F[公众号文章]
        E --> F
    end

    subgraph 谜题匹配
        G[logic_matcher.py]
        H[index.json\n机器索引]
        I[推理谜题仓库\n6个子目录]
        J[推荐结果\n谜题ID+类型+融入建议]
        K{用户决策}
        G --> H
        H --> I
        G --> J
        J --> K
    end

    subgraph 内容建设
        L[囤货\n33IQ/PuzzlePicnic等]
        I -.-> L
    end

    F -. 推送成功 .-> G
    D -. 搜索 prompt 含 .->|隐含的逻辑矛盾或两难选择| E
    K -. 决定融入 .-> F
```

## 核心组件

### 1. 谜题仓库（数据层）
- **位置**: `world-corner-blog/reasoning-library/`，与博客同仓库
- **目录结构**: 按谜题类型分 6 个子目录 —— `deduction/`（纯逻辑推理）、`grid-puzzle/`（网格排除）、`lateral-thinking/`（横向思维）、`pattern/`（图形/序列/归纳）、`strategy/`（博弈/决策）、`life-analogy/`（可映射到现实生活）
- **每个谜题文件**: Markdown + Frontmatter（id, title, type, source, tags, keywords, difficulty, mappings），其中 `mappings` 是核心关联字段，标记该题可映射到的文章主题（如"AI工具选择""信息甄别"）
- **`index.json`**: 整库的机器检索索引，收录 id + title + tags + keywords + mappings，供匹配脚本快速全文搜索

### 2. 匹配引擎（逻辑层）
- **`logic_matcher.py`**: 分析已完成的文章标题和前 200 字，提取关键词，检索 `index.json`，输出最匹配的谜题 ID、类型和融入建议
- **匹配输入**: 文章关键词 OR 指定文章文件路径
- **匹配输出**: 谜题 ID + 类型 + 融入建议（如何在文章对应段落自然嵌入）

### 3. 管线集成（触发层）
- **`publish_one.py`**（公众号一键发布管线）: 每次发布后自动触发 `logic_matcher.py`
- **content-orchestrator**（三AI协作管线）: 在 Step 1（AI选题）与 Step 2（DeepSeek搜索）之间嵌入"逻辑矛盾或两难选择"提取环节
- **发布搜索 prompt 增强**: 每次发文的 DeepSeek 搜索 prompt 永久加入"隐含的逻辑矛盾或两难选择"要求

### 组件关系
```
publish_one.py ──推送成功──▶ logic_matcher.py ──搜索──▶ index.json
       │                                                        │
       ▼                                                        ▼
content-orchestrator                                       推理谜题文件
(Step1→矛盾提取→Step2)                                 (6个子目录)
```

## 数据流

### 主流程（文章发布后自动触发）
1. **输入**: `publish_one.py` 推送公众号文章成功
2. **触发**: 自动调用 `logic_matcher.py`，无需用户干预
3. **关键词提取**: 从文章标题或前 200 字提取核心关键词
4. **索引检索**: 以关键词搜索 `index.json`，按 tags/keywords/mappings 匹配
5. **推荐输出**: 返回最匹配的谜题（ID + 类型 + 融入建议，如"可在第 X 段插入这个两难选择")
6. **人工决策**: 用户审阅推荐结果，决定是否融入、如何融入

### 囤货流程（内容建设）
- 手动/半自动从 33IQ、PuzzlePicnic、BrainBashers、gridpuzz 等网站收集经典谜题
- 写入对应类型子目录，同时更新 `index.json`

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| **仓库归属** | 与博客同仓库（`world-corner-blog/reasoning-library/`） | 谜题与文章强绑定，同仓库便于管线集成和匹配引用 |
| **匹配时机** | 文章写完后（后置匹配） | 不限制文章写作自由度，避免"先有谜题再凑文章"的生硬感 |
| **关联机制** | `mappings` 字段桥接谜题和文章主题 | 绕过纯关键词匹配的语义鸿沟，人工标注的映射关系更精准 |
| **执行模式** | 自动触发而非用户手动调用 | 发布成功后自动跑匹配，降低用户心智负担 |
| **搜索增强** | 永久嵌入 publish prompt | 从选题阶段开始制造"逻辑矛盾"素材，让 AI 写作时自然埋下伏笔 |
| **不独立建库** | 不另开 GitHub 仓库 | 避免多仓库维护成本，与博客共用版本管理 |

## 优化方向

| 方向 | 具体措施 | 优先级 |
|------|----------|--------|
| **内容填充** | 按目录结构填充 5-7 道经典谜题（每种类型至少 1 道），含完整 frontmatter 和 mappings | P0（阻塞后续步骤） |
| **匹配脚本** | 完成 `logic_matcher.py` 开发：支持关键词匹配和文章文件匹配两种模式 | P0 |
| **管线集成** | `publish_one.py` 新增 `--推理` 标志，发布后自动触发匹配 | P1 |
| **搜索 prompt 增强** | 更新 publish_one 中 DeepSeek 搜索 prompt，永久加入"隐含的逻辑矛盾或两难选择" | P1 |
| **content-orchestrator 增强** | 在 Step 1→2 之间插入矛盾提取环节，让后续搜索和起草都有逻辑冲突素材 | P2 |
| **来源扩展** | 中文源（33IQ、贝克街推理学院、gridpuzz 中文站）+ 英文源（ZebraPuzzles、BrainBashers、PuzzlePicnic）常态化收集流程 | P2 |
| **融入质量评估** | 后期可引入 A/B 测试指标：带谜题文章 vs 不带谜题文章的阅读完成率/互动率 | P3 |

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/projects/reasoning-library-design.md`*
