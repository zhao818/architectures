# 视频生成管线 V1 (Video Pipeline System) 架构

> 一键式视频生成管线，基于 Remotion 渲染引擎，将文本标题/文章自动转化为完整短视频。输入标题和配置项，经钩子分析、素材生成、音频合成、视频渲染 6 步管线，产出最终视频文件并写入注册表。支持技能触发（Claude 内用 `video-pipeline` 技能）和 CLI 直接调用。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        video_pipeline.py                            │
│                 管线调度器（PipelineTracker 可视化）                    │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      │
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐ │
│hook  ││artic││asset││tts  ││rende││regis│ │
│     ││les  ││s    ││     ││r    ││try  │ │
└──┬──┘└─────┘└──┬──┘└──┬──┘└──┬──┘└─────┘ │
   │             │     │     │              │
   ▼             │     ▼     ▼              │
┌────────┐       │  ┌──────────────┐        │
│hooks   │       │  │generate_bat │        │
│.json   │       │  │ch_final.py  │        │
└────────┘       │  │ (TTS + BGM) │        │
                 │  └──────────────┘        │
┌──────────┐     │                         │
│suggest_ho│     │  ┌─────────────────┐    │
│ok.py     │     │  │PromoVideo.tsx   │    │
└──────────┘     │  │  ┌───────────┐  │    │
                 │  │  │HookIntro  │  │    │
┌───────────┐    │  │  │.tsx       │  │    │
│generate_as│────┘  │  └───────────┘  │    │
│sets.py    │       │  │ AssetBackgrou│    │
│(Pillow,   │       │  │ nd (fallback)│    │
│ 10 themes)│       │  └─────────────┘    │
└───────────┘       └─────────────────────┘

┌──────────────────────────────┐
│ collect_video_stats.py       │  ← 独立定时任务
│ (B站/抖音 get_traffic)        │
└──────────────────────────────┘
```

## 核心组件

| 组件 | 文件 | 职责 | 依赖关系 |
|------|------|------|----------|
| **管线调度器** | `video_pipeline.py` | 编排 6 步管线（hook → articles → assets → tts → render → registry），集成 PipelineTracker 终端可视化 | 调用下游所有组件 |
| **钩子分析器** | `suggest_hook.py` | 解析文章内容，从 8 种钩子公式中推荐最佳开头（前 3 秒），生成对应文案配置 | 读取 `hooks.json` |
| **钩子公式库** | `hooks.json` | 8 种钩子的 TTS 模板 + 视觉风格 + 示例数据 | 被 suggest_hook 读取 |
| **素材生成器** | `generate_assets.py` | Pillow 生成封面图和背景图，提供 10 套可选主题 | 被管线调度器调用 |
| **音频合成器** | `generate_batch_final.py` | TTS + BGM 音频生成，已接入钩子感知（根据钩子类型调整语调和音效） | 依赖 suggest_hook 输出的钩子配置 |
| **Remotion 视觉组件** | `HookIntro.tsx` | 前 3 秒钩子视觉效果，对应钩子公式库的视觉风格 | 被 PromoVideo 引用 |
| **Remotion 主合成** | `PromoVideo.tsx` | 支持 AssetBackground 模式——有素材用素材，无素材回退代码渲染 | 引入 HookIntro 及其他场景组件 |
| **数据采集器** | `collect_video_stats.py` | 定时采集 B 站/抖音视频播放数据（B站/抖音 `get_traffic`） | 独立运行，不参与管线 |

## 数据流

1. **输入** → CLI 参数（标题、副标题、卡片数据、主题、金句）或技能调用
2. **Step 1: hook** → suggest_hook.py 分析文章 → 从 hooks.json 匹配最优钩子类型 → 输出钩子文案配置
3. **Step 2: articles** → 文章内容处理（管线步骤名暗示文章解析/卡片组装）
4. **Step 3: assets** → generate_assets.py 根据主题生成封面图片 + 背景图片（Pillow 渲染）
5. **Step 4: tts** → generate_batch_final.py 合成 TTS 语音 + BGM，钩子感知调整语气
6. **Step 5: render** → Remotion 合成视频（PromoVideo.tsx 读取素材/钩子配置 → 视频帧渲染输出）
7. **Step 6: registry** → 输出信息写入注册表，记录视频元数据
8. **旁路** → collect_video_stats.py 独立定时采集发布后的播放数据

终端可视化：PipelineTracker 实时显示 ◉⏳→●✅ 状态流转，每步完成即更新。

## 关键设计决策

1. **钩子系统（8 种公式）** — 将视频开头 3 秒结构化为一组可枚举的钩子公式库（TTS 模板 + 视觉风格 + 示例），而非自由创作，保证开头质量和一致性
2. **素材回退机制** — `PromoVideo.tsx` 支持双模式：有素材文件时用 AssetBackground，无素材时自动回退代码渲染背景，提升管线鲁棒性
3. **10 套主题体系** — `generate_assets.py` 内置 10 套视觉主题，通过 `--theme` 参数切换，实现视觉多样性而不增加复杂度
4. **PipelineTracker 集成** — 6 步管线实时终端可视化，便于调试和观察进度
5. **CLI 优先设计** — 管线入口为命令行工具，参数化标题/副标题/卡片/主题/金句，支持 `--skip-assets` 跳过素材步骤，灵活适配不同场景
6. **技能封装** — 封装为 `video-pipeline` Claude 技能，触发词为「生成视频」「做视频」「视频管线」「素材生成」「视频封面」，可在对话中直接调用
7. **数据采集分离** — 视频发布后的效果跟踪者独立为 `collect_video_stats.py` 定时任务，不耦合在渲染管线中

## 优化方向

1. **Python import 路径修复** — 文件命名连字符问题：`pipeline-tracker.py`→`pipeline_tracker.py`，避免 Python import 失败。后续新建脚本统一用下划线命名
2. **TTS 钩子量化双单位 bug** — `generate_batch_final.py` 中 `customText` 已含单位时不应重复提取，需要空值判断逻辑
3. **B 站/抖音流量模块导入** — `collect_video_stats.py` 需确保 `from .traffic import get_traffic` 正确导入，避免 NameError
4. **素材跳过机制** — `--skip-assets` 标记在具体组件中的联动逻辑需验证，跳过素材后背景渲染是否仍能正常工作
5. **钩子感知 TTS** — 钩子类型→TTS 语气映射需扩展更多钩子类型覆盖，目前 8 种可能不足以应对多样化内容

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/projects/video-pipeline-system.md`*
