# Workflow — 架构仓库使用流程

## 什么时候用

- 要记录一个新系统的架构设计
- 要对现有系统做优化提案
- 要做技术选型决策（ADR）
- 看到好的架构想收藏参考

## 标准流程

### 新增系统架构

```
① 在 systems/ 下创建目录
② 写 README.md（参考 templates/system-README.md）
③ 如需画图，放 diagrams/（PlantUML/draw.io）
④ git add → commit → push
```

### 提出优化方案

```
① 在 systems/<name>/proposals/ 写提案（参考 templates/proposal.md）
② 标记状态为"提议"
③ 评审后改为"已实施"或"已放弃"
```

### 记录架构决策

```
① 在 adr/ 创建 adr-<NNN>-<slug>.md（参考 templates/adr.md）
② 标记状态：提议/已采纳/已弃用/已取代
③ 更新 adr/INDEX.md
```

### 收集外部参考

```
① 把链接或原文放 references/
② 写简要说明：为什么值得参考
```

## 结构

| 目录 | 用途 |
|------|------|
| systems/ | 各系统的当前架构 + 优化提案 |
| patterns/ | 跨系统的通用架构模式 |
| adr/ | 架构决策记录 |
| references/ | 外部优秀架构参考 |
| diagrams/ | 架构图源文件 |
| templates/ | 文档模板 |
