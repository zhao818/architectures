# Architecture Designs

系统架构设计仓库。

## 用途

- **存档** — 记录所有系统的当前架构设计
- **优化** — 对现有架构提出改进方案，跟踪演进历史
- **参考** — 收集外部优秀的架构设计模式，随时借鉴

## 结构

```
architectures/
├── systems/          # 具体系统架构（按系统分目录）
│   ├── reasonix/
│   ├── text-to-cad/
│   ├── content-orchestrator/
│   └── publishing-pipeline/
├── patterns/         # 跨系统架构模式
├── references/       # 外部优秀架构参考
├── adr/              # Architecture Decision Records
├── diagrams/         # 架构图源文件
└── templates/        # 新增文档模板
```

## 索引

详见 [INDEX.md](./INDEX.md)

## 使用方式

### 新增系统架构
```
systems/<name>/
├── README.md         # 架构总览（当前状态）
├── v1.md             # 历史版本（可选）
└── proposals/        # 优化提案（可选）
```

### 新增 ADR
```
adr/adr-<NNN>-<slug>.md
```

### 新增模式
```
patterns/<slug>.md
```

参考 `templates/` 目录下的模板文件。
