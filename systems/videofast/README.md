# VideoFast Full-Loop Verified Architecture 架构

> VideoFast is a serverless video generation platform that accepts orders from a static frontend, orchestrates a multi-step video production pipeline (hook scraping, asset preparation, TTS audio generation, Remotion rendering), and delivers the final MP4 via email. The verified end-to-end loop processes an order in approximately 2.5 minutes, producing 1080x1920 output.

## 架构概览

```
┌──────────────┐     POST /videofast/order     ┌──────────────────────────┐
│  Vercel      │ ────────────────────────────▶ │  CF Worker               │
│  Static Page │                               │  api.worldcorner.xyz     │
│  (video.     │                               │                          │
│   worldcorner│                               │  PATCH /videofast/order/ │
│   .xyz)      │ ◀──────────────────────────── │  {id} (status callback)  │
└──────────────┘                               └──────────┬───────────────┘
                                                          │
                                                          ▼
                                                  ┌──────────────────┐
                                                  │  Cloudflare KV    │
                                                  │  (Order Queue +   │
                                                  │   State Store)    │
                                                  └──────────┬───────────┘
                                                          │
                                              Polls for new orders
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Flask Orchestrator (:5001)  ──  videofast_server.py                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  video_pipeline.py (6-step)                                     │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐  ┌───────────┐   │   │
│  │  │ hook │→│assets│→│ TTS  │→│ Remotion │→│ deliver  │   │   │
│  │  │      │  │      │  │      │  │ (1080×   │  │ (Gmail   │   │   │
│  │  │      │  │      │  │      │  │  1920)   │  │  SMTP)   │   │   │
│  │  └──────┘  └──────┘  └──────┘  └──────────┘  └───────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心组件

## Five-Layer Architecture

1. **Vercel Static Frontend** (`video.worldcorner.xyz`)
   - Serves the user-facing order submission page
   - Statically hosted, zero backend — posts orders directly to the CF Worker API

2. **Cloudflare Worker + KV** (`api.worldcorner.xyz/videofast/order`)
   - **CF Worker**: Serverless API gateway that accepts incoming video orders and exposes a PATCH endpoint for status write-back
   - **KV Store**: Persistent order queue and state store (processing / done / failed), decouples frontend from backend processing

3. **Flask Orchestrator** (`videofast_server.py`, port 5001)
   - Polls Cloudflare KV for new orders on a loop
   - Dispatches each order to the pipeline; acts as the glue layer between the serverless API and the local rendering stack
   - Exposes a health check endpoint (`/videofast/health`)

4. **Video Pipeline** (`video_pipeline.py`)
   - 6-step sequential pipeline: `hook → assets → TTS → Remotion → ...`
   - `hook`: scrapes or fetches source content
   - `assets`: prepares media assets (images, fonts, overlays)
   - `TTS`: generates voiceover audio
   - `Remotion`: renders final 1080x1920 MP4 video programmatically via React

5. **Gmail SMTP Notification**
   - Sends the completed MP4 (or failure alert) to the user via email
   - Closes the notification loop back to the customer

**Relationships**: The architecture follows a strict producer-consumer chain. The Vercel frontend (producer) writes to KV via CF Worker. The Flask service (consumer) polls KV, runs the pipeline, and writes status back to KV via the Worker's PATCH endpoint. Each layer is independently deployable and communicates over HTTP.

## 数据流

```
User Browser
    │
    ▼
① Vercel Static Page (video.worldcorner.xyz)
    │  POST /videofast/order
    ▼
② CF Worker (api.worldcorner.xyz/videofast/order)
    │  Writes order to KV
    ▼
③ Cloudflare KV Store
    │  Order persisted with status: processing
    │  ▲
    │  │ Polls every N seconds
    │  │
④ Flask Orchestrator (:5001)
    │  Reads new order from KV
    ▼
⑤ video_pipeline.py (6-step pipeline)
    └─ hook      → fetch source content
    └─ assets    → prepare media assets
    └─ TTS       → generate voiceover audio
    └─ Remotion  → render MP4 (1080×1920, ~1.8MB)
    │
    ▼
⑥ Gmail SMTP → sends MP4 to user
    │
    ▼
Flask calls PATCH /videofast/order/{id}
    │  Writes status: done (or failed + retry)
    ▼
② CF Worker updates KV
    │  User can poll status from frontend
    ▼
KV status: done
```

**End-to-end latency (verified)**: ~2.5 minutes from order submission to delivery email (vf_05953590).

## 关键设计决策

1. **Serverless API + Polling Worker pattern**: Using CF Worker+KV as the order ingress (no persistent server needed at the edge), while a local Flask service polls for work. This decouples the public API surface from the compute-heavy rendering backend.

2. **KV as shared state, not just queue**: CF KV serves double duty — it is both the order queue and the persistent state store (processing/done/failed). This eliminates the need for a dedicated database or message broker.

3. **State machine with retry (3 states)**: `processing → done | failed`. Failed orders are retried rather than dropped, a fix from an earlier bug where failures were silent.

4. **KV status write-back via PATCH**: The Flask service updates order status back to KV through the CF Worker's PATCH endpoint, enabling the frontend (and monitoring) to track order lifecycle. This was a bug fix — earlier versions did not write status back.

5. **Remotion for programmatic video rendering**: Chose Remotion (React-based video framework) over traditional video editing tools, giving full programmatic control over the final 1080x1920 output with precise frame-level composition.

6. **Gmail SMTP as delivery channel**: Simple, no-infrastructure notification — no need for WebSocket connections, push notification services, or a custom dashboard.

## 优化方向

1. **Local render queue consumption (fixed)**: The original design had a `_render_queue` that was never consumed, causing orders to pile up. Fixed by having the worker consume both KV and local queue entries.

2. **Failure resilience with state machine**: Added explicit `processing → done/failed` transitions with retry logic, replacing a silent-failure model. Next step could be exponential backoff or dead-letter queues for persistently failing orders.

3. **KV status synchronization**: Status write-back via PATCH ensures the frontend reflects real order state. Could be extended with webhook notifications or server-sent events for real-time UI updates without polling.

4. **Scalability**: Current architecture is single-worker (one Flask instance polling KV). To scale horizontally, multiple Flask workers could be added behind a simple lock or lease mechanism on KV.

5. **Monitoring**: No built-in observability beyond the health endpoint. Adding structured logging and metrics (order count, pipeline step duration, failure rate) would improve operational visibility.

6. **Cold start / Remotion rendering time**: At 2.5 minutes per video, Remotion rendering is the bottleneck. Caching intermediate assets and TTS audio, or pre-warming the Remotion bundle, could reduce latency.

7. **Order deduplication**: KV-based polling could produce duplicate processing under concurrent workers. Adding idempotency keys or atomic CAS operations would prevent double-rendering.

---
*此文档由 claude-memory 迁移生成，原始来源：`claude-memory/projects/videofast-full-loop-verified.md`*
