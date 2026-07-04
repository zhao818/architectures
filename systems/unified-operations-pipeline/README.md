# Unified Operations Pipeline V4 架构

> A single-command content operation pipeline that, triggered by the phrase "开始运营" (start operations), orchestrates the full lifecycle of content creation and distribution: community research to improve the framework, intelligence gathering from multiple sources, AI-assisted article drafting via a content fusion methodology, mandatory quality evaluation, multi-platform text distribution (5 platforms), short-video generation and distribution (5 platforms), monetization (Xianyu e-commerce), and automatic experience extraction for continuous improvement. The pipeline wraps all steps in a visual tracker with anti-detection layers and error-handling hints — all behind a single user utterance.

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER TRIGGER: "开始运营"                          │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      PipelineTracker (Visual Progress)                   │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                     FDE Methodology (6-step loop)                │   │
│   └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│  ⓪ Research  │    │  ① Intel         │    │  ② Topic Select   │
│ yuanbao_py   │───▶│ yuanbao_py intel │───▶│ Content Fusion    │
│ research     │    │ 4 channels       │    │ Framework A/B/C/D │
│ (framework)  │    │ → learning-      │    └────────┬──────────┘
└──────────────┘    │   journal.md     │             │
                    └──────────────────┘             │
                           intel_context             │
                           (as_dict=True)            │
                    ┌──────────────────┐             │
                    │  ③ Draft         │◀────────────┘
                    │ yuanbao_py draft │
                    │ SCQA + brand HTML│
                    │ → WeChat API     │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
              ◀──── │  ④ Eval Gate     │
              retry │ t2cad_eval ≥90%  │
                    └────────┬─────────┘
                             │ PASS
                    ┌────────▼─────────┐
                    │  ⑤ Text Dist.    │
                    │ publish.py       │
                    │ ┌─ Zhihu         │
                    │ ├─ Juejin +auto  │
                    │ ├─ Bili column   │
                    │ ├─ Tencent Cloud │
                    │ └─ Jike          │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  ⑥ Video Gen     │
                    │ Remotion TTS+BGM │
                    │ → 1080×1920 MP4  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  ⑦ Video Dist.   │
                    │ Playwright+stealth│
                    │ ┌─ Douyin        │
                    │ ├─ Kuaishou      │
                    │ ├─ Bilibili      │
                    │ ├─ Video Account │
                    │ └─ Xiaohongshu   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  ⑧ Monetization  │
                    │ Goofish publish  │
                    │ + delivery --watch│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  ⑨ Post-mortem   │
                    │ extract-         │
                    │ instincts.py     │
                    │ → claude-memory/  │
                    │ → pitfall cards  │
                    └──────────────────┘

Cross-cutting layers (applied to every Playwright step):
┌────────────────────────────────────────────────────────────────┐
│ 🛡️ Anti-detection: playwright-stealth + SessionPersona        │
│    (1 persona per platform, randomized fingerprints)           │
├────────────────────────────────────────────────────────────────┤
│ 📊 PipelineTracker: real-time step status + error context      │
│    + KNOWN_HINTS teacher hints                                 │
├────────────────────────────────────────────────────────────────┤
│ 🧠 FDE Methodology: 6-step closed loop governing all decisions │
└────────────────────────────────────────────────────────────────┘

No. of platforms: 12 total (1 WeChat base + 5 text traffic + 5 video traffic + 1 e-commerce)
```

## 核心组件

The architecture comprises 10 linearly ordered steps (0-9), each backed by dedicated scripts or modules, orchestrated by a LangGraph StateGraph DAG (pipeline_dag.py, later deleted) and visualized via PipelineTracker.

**Core orchestration layer:**
- **PipelineTracker** — Terminal-based real-time step status panel that shows which step is running, succeeded, or failed, with error context and teacher hints (KNOWN_ISSUES dictionary for common failures like HTTP 500, SSL, encoding).
- **Pipeline DAG (pipeline_dag.py)** — LangGraph StateGraph with conditional branching, parallel execution, human-in-the-loop checkpoints, and resume-from-failure support. Deleted in the final iteration, replaced by simpler one-shot scripts (publish_one.py).
- **FDE Methodology** — Governing theoretical framework: a 6-step closed loop (Research-define-prototype-produce-deploy-settle), 4 principles (including "no eval = not done"), and 5 maturity levels.

**Content creation layer (steps 0-3):**
- **yuanbao_pipeline.py** — Three sub-commands using Tencent Yuanbao search: `research` (scan mature AI operation frameworks for optimization ideas, stores to learning-journal.md), `intel` (4-channel automatic search for trending topics, competitor analysis, Zhihu long-tail questions, cross-platform trends), `draft` (loads the Content Fusion Framework as kernel, generates SCQA-structured draft with headline ≤9 chars + summary ≤17 chars + golden-quote ✦). The `full` command chains all three into one call.
- **Content Fusion Framework** — 4 creative modes: A=热点→哲学 (trend to philosophy), B=技术→人文 (tech to humanity), C=思想人物→技术 (thinker to tech), D=跨界碰撞 (cross-boundary collision). Provides the structural kernel for drafting.
- **zhihu_answer_search.py** — Standalone script that automatically searches for high-view/low-answer Zhihu long-tail questions, matches against content pool, and generates draft answers for SEO traffic.

**Quality layer (step 4):**
- **t2cad_eval.py** — Four-dimension scoring system: grammar, safety, task-match, code-quality. Composite score ≥90% required for release. Maintains eval history for regression tracking across prompt iterations. Acts as a hard gate (not optional per FDE principle 3).

**Distribution layer (steps 5-7):**
- **publish.py** — Multi-platform text distribution supporting Zhihu (Playwright + Draft.js), Juejin (API + Cookie), Bilibili column (API + Cookie), Tencent Cloud Community (Playwright + Draft.js, with auto "recommend to homepage" click after publish), Jike/即刻 (Playwright + Lexical). All Playwright-based platforms load anti-detection layer (`playwright-stealth` + SessionPersona random persona system).
- **Juejin self-interaction** — After publish, auto-open browser → navigate to article → like + bookmark to trigger Feed push.
- **Remotion Video Pipeline** — Reads articles from data/articles.json, generates TTS audio + BGM via templates/generate_batch_final.py, renders 1080x1920 portrait 25s videos via `npx remotion render`.
- **Video distribution** — Playwright + stealth for Douyin, Kuaishou, Bilibili, WeChat Video Account (Shadow DOM piercing fix), Xiaohongshu (Shadow DOM repair fix).

**Monetization layer (step 8):**
- **Goofish (Xianyu) listing** — Playwright + stealth auto-publish product listings with brand cover (800x800).
- **goofish_delivery.py --watch** — Background daemon polling every 5 minutes for paid orders, auto-sends download links.

**Feedback/improvement layer (step 9):**
- **extract-instincts.py** — Scans the session transcript to auto-extract pitfalls and operational patterns, generates new memory cards into claude-memory/pitfalls/.
- Manual steps: update topic pool, clean temp files, record data tracking baseline, write learnings to claude-memory/ via FDE settlement.

**Cross-cutting infrastructure:**
- **Anti-detection system** — Unified `playwright-stealth` + SessionPersona (randomized browser fingerprint, user agent, viewport, mouse trajectory patterns per session, one persona per platform to avoid cross-platform correlation).
- **Platform style adapter** — Pre-publish style normalization (different word count, tone, formatting per platform).
- **WeChat operation workflow** — The publishing chain for the main base (WeChat Official Account): HTML template (deep blue #1a1a2e + warm gold #c8a03c) → API draft push → user scans QR code to mass-send.

## 数据流

```
User trigger ("开始运营")
  │
  └─ PipelineTracker wraps all steps
      │
      ├─ ⓪ Research (yuanbao_pipeline.py research)
      │   → writes learning-journal.md (framework improvements)
      │
      ├─ ① Intel (yuanbao_pipeline.py intel)
      │   → writes learning-journal.md (trends, competitors, long-tail questions)
      │
      ├─ ② Topic Selection (Content Fusion Framework)
      │   → selects one of 4 modes (A/B/C/D) based on intel + content pool
      │
      ├─ ③ Draft (yuanbao_pipeline.py draft)
      │   → loads Content Fusion + intel context → SCQA draft
      │   → human polishes → brand HTML template → WeChat API draft push
      │
      ├─ ④ Eval Gate (t2cad_eval.py)
      │   → 4-dimension score ≥90%? → YES=continue, NO=return to step ③
      │
      ├─ ⑤ Text Distribution (publish.py)
      │   → Zhihu / Juejin / Bilibili / Tencent Cloud / Jike
      │   → Tencent Cloud: auto "recommend" click
      │   → Juejin: auto like+bookmark for feed push
      │
      ├─ ⑥ Video Generation (Remotion pipeline)
      │   → data/articles.json → TTS+BGM → 1080×1920 MP4
      │
      ├─ ⑦ Video Distribution (Playwright + stealth)
      │   → Douyin / Kuaishou / Bilibili / Video Account / Xiaohongshu
      │
      ├─ ⑧ E-commerce (Goofish)
      │   → auto publish listing + start --watch background delivery monitor
      │
      └─ ⑨ Post-mortem
          → extract-instincts.py: session → pitfalls/*.md + claude-memory/
          → update topic pool, clean temp files, record analytics baseline

Data coupling:
- V4 critical fix: intel output is passed as structured context (as_dict=True, auto_extract=True) to the draft step, not just written to disk independently.
- Research output only updates the framework, does NOT directly feed draft context.
- The Eval gate creates a feedback loop: <90% → return to drafting step for revision.
- Post-mortem closes the loop: operational insights → claude-memory/ → future sessions automatically load fewer pitfalls.
```

## 关键设计决策

1. **Freeze-and-extend (steps ⑤-⑨ untouchable)** — The proven distribution and monetization pipeline (steps 5-9) was declared frozen: "只融不改，不重做" (only integrate, don't redo). Innovation is confined to the front-end content creation steps (0-4). This is a deliberate risk-reduction strategy to protect working revenue-generating flows.

2. **Data flow as the V4 breakthrough** — Previous versions (V3) called Yuanbao's three sub-commands independently: intelligence was gathered but never fed into drafting. V4's defining architectural change was passing structured `intel_context` from `intel` to `draft` — the data actually flows. This recognizes that composition without data coupling is just sequential execution.

3. **Quality gate as a hard constraint** — The eval gate (≥90%) is non-negotiable per FDE principle 3: "any LLM output without eval verification is not done." This trades throughput for consistency and enforces a 3-round retry loop for substandard drafts. The gate has version history tracking to prevent prompt regression.

4. **Single-point-of-trigger with visual progress** — The user says one phrase ("开始运营") and PipelineTracker handles the rest. Every step is visible in the terminal with status, elapsed time, and error context. This reduces cognitive load and provides immediate failure localization without digging through logs.

5. **Anti-detection as a cross-cutting layer, not a per-platform concern** — Instead of each Playwright script handling its own stealth, the system provides a unified `playwright-stealth` + SessionPersona layer. One persona per platform to prevent cross-platform correlation. This is essential for platforms (Zhihu, Tencent Cloud, Douyin, etc.) that detect automation.

6. **Content Fusion (借壳生蛋) as the creative engine** — Rather than generating content from scratch, the system applies 4 transformation modes that combine existing popular frames with the user's domain expertise. This is a structural pattern (not prompt tuning) designed to produce differentiated content while riding existing traffic patterns.

7. **WeChat as hub, all else as traffic spokes** — The WeChat Official Account is the only platform where the user's brand identity lives (deep blue + warm gold HTML). All other platforms (5 text + 5 video) are explicitly labeled SOFT_TRAFFIC — designed to redirect readers to the WeChat base. Monetization (Xianyu) is a separate channel. This prevents brand fragmentation across 12 platforms.

8. **Subsequent simplification recognized the overhead** — The pipeline V4 was later superseded by the `wechat-publish` skill + `publish_one.py` (single-script for one-click publishing). The DAG orchestration (pipeline_dag.py) was deleted entirely. The system evolved from a heavy 10-step LangGraph pipeline to a lightweight skill-based approach — indicating the full pipeline was too rigid for daily use.

## 优化方向

1. **Supersession itself is the strongest signal** — The entire pipeline was marked superseded within one day (2026-06-28 to 2026-06-29), replaced by a single-script approach (`publish_one.py`) + modular skill (`wechat-publish`). The LangGraph DAG was deleted. This suggests the 10-step orchestration was too heavy for daily operation — the optimization direction was radical simplification: remove the orchestrator, keep the scripts callable directly.

2. **Human-in-the-loop friction** — Step ③ requires "人工细化润色" (human refinement and polishing) between draft and eval, and final publication requires the user to scan a QR code to mass-send on WeChat. The pipeline cannot fully automate the core loop. Optimization direction: reduce human touchpoints or make them parallelizable (e.g., refine while video renders).

3. **Anti-detection fragility** — Playwright-based platforms rely on stealth + SessionPersona, which are cat-and-mouse games against platform detection upgrades. Each platform (especially Douyin and Xiaohongshu) likely needs ongoing maintenance. The Xiaohongshu Shadow DOM fix is already a known pain point. Optimization direction: centralize detection failure monitoring and auto-update stealth parameters.

4. **No analytics feedback loop** — Step ⑨ mentions "记录数据追踪起点" (record analytics baseline) but there is no systematic performance analytics pipeline that feeds back into topic selection (step ②) — i.e., which topics actually drove traffic/ monetization from the last cycle. The FDE methodology's "settle" step is mostly manual.

5. **Monetization-disconnect** — Goofish (step ⑧) runs independently after content distribution. There is no integration between content topics and what products are listed. Optimization direction: auto-generate product listings from article content (e.g., "if article is about Claude Code tips, auto-create a 'Claude Code prompt pack' listing").

6. **Intra-pipeline redundancy** — Steps ⓪ (research) and ① (intel) both write to `learning-journal.md` and both use `yuanbao_pipeline.py`. Research optimizes the framework while intel feeds the draft — but they share the same search backend. Merging or at least caching research results into intel could save API calls.

7. **Error recovery still manual** — PipelineTracker shows error context and KNOWN_HINTS, but recovery requires human intervention. No automatic retry with backoff, no automatic credential refresh, no session checkpoint-and-resume for the full pipeline (only the DAG had this and it was deleted).

8. **Token/cost visibility** — No mention of tracking API consumption (Yuanbao search API, DeepSeek for drafting, Remotion rendering costs). With 12 platforms and multiple AI calls per cycle, cost observability would prevent surprise bills.

9. **Persona rotation staleness** — SessionPersona assigns one persona per platform per session. Over repeated operations, the same persona set would be reused, increasing cross-session correlation risk. Optimization: persona expiration + regeneration after N uses.

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/global/workflows/unified-operations-pipeline.md`*
