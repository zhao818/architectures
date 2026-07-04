# Anti-Detection System (3-Layer Protection) 架构

> Prevent automated content-publishing scripts from being detected as bots by target web platforms. The system uses a layered deception approach to make Playwright-driven browser sessions appear as human-operated, covering browser fingerprint evasion, human-like interaction patterns, and session-level behavioral personality. It supports 11 platforms (Tencent Cloud, Zhihu, Xiaohongshu, Jike, Xianyu, Douyin, Kuaishou, Channels, Bilibili, Juejin, WeChat) with live browsers for the first 9 and API-only for Juejin/WeChat.

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                   Platform Classes                           │
│  (zhihu, xiaohongshu, douyin, kuaishou, bilibili, ...)       │
│         │ each inherits from BasePlatform                     │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  BasePlatform (platforms/base.py)                            │
│                                                              │
│  ┌─────────────────────────────────────────┐                │
│  │  __init__()                              │                │
│  │  1. random session persona (L3)          │                │
│  │  2. randomize viewport (L1)              │                │
│  └──────────┬──────────────────────────────┘                │
│             │                                                │
│  ┌──────────▼──────────────────────────────┐                │
│  │  _apply_stealth(page) [L1]              │                │
│  │  → playwright-stealth fingerprint patch  │                │
│  └──────────┬──────────────────────────────┘                │
│             │                                                │
│  ┌──────────▼──────────────────────────────┐                │
│  │  Human Interaction Methods [L2]         │                │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────┐  │                │
│  │  │ human_   │ │ human_   │ │ human_  │  │                │
│  │  │ delay()  │ │ type()   │ │ scroll()│  │                │
│  │  └────┬─────┘ └────┬─────┘ └────┬────┘  │                │
│  │  ┌──────────┐ ┌──────────┐              │                │
│  │  │ human_   │ │ random_  │              │                │
│  │  │ click()  │ │ fidget() │              │                │
│  │  └────┬─────┘ └────┬─────┘              │                │
│  └───────┼────────────┼────────────────────┘                │
│          │            │                                      │
│          ▼            ▼                                      │
│  ┌─────────────────────────────────────────┐                │
│  │  SessionPersona [L3]                     │                │
│  │  ├── 急躁型: fast, few errors, impatient  │                │
│  │  ├── 思考型: slow, more errors, hesitant   │                │
│  │  └── 细致型: moderate, careful            │                │
│  │  → drives parameters for all _human_*()   │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Platform: Browser   │      │  Platform: API-only   │
│  (9 live platforms)  │      │  (juejin, wechat)     │
│  L1+L2+L3 active     │      │  No anti-detection     │
└──────────────────────┘      └──────────────────────┘
```

## 核心组件

**Layer 1 — Unified Stealth (`base.py` → `_apply_stealth()`, `_randomize_viewport()`)**: Applies `playwright-stealth` to cover all detectable browser fingerprints (navigator.webdriver, plugins, languages, hardwareConcurrency, chrome.runtime, WebGL vendor, permissions, etc.). Viewport is chosen randomly from 5 presets (1440x900, 1366x768, 1536x864, 1920x1080, 1280x720) with +/-5% jitter per session.

**Layer 2 — Behavioral Diversification (5 `_human_*` methods)**: Each interaction method uses randomized, non-uniform distributions rather than fixed or uniform delays:
- `_human_delay()` — gamma, normal, or exponential distribution (never uniform)
- `_human_type()` — persona-dependent speed + 2% typo-and-backspace rate + pause before long words
- `_human_scroll()` — random step count + 20% backtrack probability + simulated reading pause
- `_human_click()` — off-center targeting (20%-80% offset within element) + variable-speed pre-click wait
- `_random_fidget()` — persona-dependent probability of micro-scrolls, pauses, or rollbacks (hesitation signals)

**Layer 3 — Session Persona (`SessionPersona` class)**: Three predefined behavioral archetypes selected randomly per session at `BasePlatform.__init__()`:
- **急躁型 (Impatient)**: fast typing (5-20ms per char), 1% error rate, gamma delay, 15% fidget probability
- **思考型 (Thoughtful)**: slow typing (30-80ms per char), 4% error rate, exponential delay, 40% fidget probability
- **细致型 (Meticulous)**: moderate typing (15-45ms per char), 2% error rate, normal delay, 25% fidget probability

All `_human_*` method parameters are driven by the chosen persona, producing measurably different interaction signatures across sessions to defeat timing-pattern analysis.

## 数据流

1. **Session Initialization** — `BasePlatform.__init__()` selects a random `SessionPersona`, then `_randomize_viewport()` picks and jitters a viewport preset.
2. **Stealth Application** — `_apply_stealth()` patches Playwright's `page` with all `playwright-stealth` finger-print overrides before any navigation.
3. **Page Interaction Loop** — Every action (type, scroll, click, fidget, delay) delegates to its `_human_*` counterpart, which reads parameters from the active persona and samples from a non-uniform distribution.
4. **Platform-Specific Extensions** — Individual platform classes (zhihu, xiaohongshu, etc.) inherit `base.py` and call `_human_*` methods during their publishing flows. Some platforms (juejin, wechat) skip L2/L3 entirely and use API-only mode (no live browser, no anti-detection needed).

## 关键设计决策

1. **Three-layer isolation** — fingerprint (L1), timing/behavior (L2), and personality (L3) are independently replaceable. A new platform can opt into any subset.
2. **Non-uniform delay distributions** — gamma/normal/exponential instead of uniform to defeat statistical detection that flags constant or symmetrically-distributed inter-action times.
3. **Typo-and-correct mechanism** — 2% error rate with backspace-and-retry mimics genuine human mistyping patterns, a strong behavioral signal that most bot frameworks ignore.
4. **Off-center clicking** — 20-80% element-relative offsets instead of center-point clicks, bypassing simple coordinate-based bot detection.
5. **Persona-driven parameter binding** — personality is chosen once per session and drives all sub-methods, making the entire session's behavior self-consistent rather than randomly varying each action independently.
6. **Viewport jitter** — +/-5% on top of random preset selection prevents even sessions with the same preset from producing identical window dimensions.
7. **API fallback for certain platforms** — juejin and wechat use API-only mode (no browser), bypassing all three layers, acknowledging that anti-detection is unnecessary or impossible for API-based publishing.

## 优化方向

1. **Persona expansion** — the current 3-persona set is small enough that repeated sampling could show clustering; adding 2-3 more archetypes (e.g., "distracted," "power-user") would increase entropy.
2. **Session memory** — no mechanism prevents reusing the same persona on consecutive runs, allowing a short-sequence observer to profile a publication burst. A round-robin or weighted-selection tracker would help.
3. **Platform-specific calibration** — delay distributions and fidget rates are global across platforms, but different sites may have different tolerance thresholds. Per-platform parameter tuning would reduce false positives on strict platforms and avoid wasted cycles on lenient ones.
4. **Machine learning feedback loop** — currently no automated pipeline to correlate detection events (blocked sessions, CAPTCHAs) with persona/parameter choices. A logging + analysis loop could learn which configurations trigger detections on which platforms.
5. **Evolving fingerprint coverage** — `playwright-stealth` is a static library; browser fingerprinting techniques evolve. A periodic update check or integration with a fingerprint-detection validation endpoint would prevent gradual degradation.
6. **Proxy/network-layer diversity** — the current system only covers browser and behavior layers. Adding per-session proxy rotation or TLS fingerprint randomization would address IP and network-level detection.

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/global/tools/anti-detection-system.md`*
