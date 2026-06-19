# Jarvis 暑期个人学习助手平台 — 项目规则

> 本文件放在项目 `.opencode/` 目录下，OpenCode 会在本项目会话中自动加载。
> **全局规则**定义在 `GLOBAL_RULES.md`（通过 `opencode.json` instructions 注入），本文件仅补充项目特有规则。

---

## 项目信息

- **项目名称**: Jarvis — 暑期个人学习助手平台
- **技术栈**: Django 5.0 + PostgreSQL 16 + Redis 7 + Docker
- **项目路径**: `D:\Jarvis project`
- **Python**: 3.12.4 | **Docker**: 29.2.1

---

## 本项目必须遵守的规则

### 1. 复杂处理专员强制调用

涉及以下场景，**必须先加载 `complex-task-specialist` skill** 走完整 5 步流程：

- 跨 2 个及以上 App 的修改
- 数据模型变更
- 涉及生产配置的修改
- 任何 Sisyphus 觉得自己可能"直接写代码"的冲动时刻
- 用户说了"复杂"、"审查"、"生产"、"上线"、"交付"等关键词

### 2. 完整生产就绪 Checklist

每次项目交付前，执行 `GLOBAL_RULES.md` 中定义的 5 大类生产就绪 Checklist。
Jarvis 项目已知的 Checklist 状态（截至 2026-06-09 Phase 1+2 审查）：

- ✅ **已通过**: 12 项（密钥环境变量/CSRF/HTTPS/安全标头/迁移/部署脚本/优雅停机/依赖锁定/错误页面）
- 🔴 **P0 阻塞**: 6 项（邮件服务/ALLOWED_HOSTS/静态文件/限流/健康检查/Sentry）— **已修复，但新阶段需重新验证**
- 🟡 **P1 建议**: 2 项（CONN_MAX_AGE/日志持久化）— **已修复**
- ⬜ **未检查**: 8 项（回滚/备份/索引/慢查询/加密/缓存/监控/SSL/合规）

### 3. 审查不可跳过

- 严格遵循 `auto-review-rules.md` 的触发矩阵
- 每次 Step 5 验收必须包含 `review-work` 5 Agent 并行审查 + Oracle 深度审查 + 生产就绪 Checklist
- 审查 FAIL 必须修复，禁止绕过

### 4. 代码修改规范

- 核心代码必须通过 `task()` 派发给子 Agent 执行，Sisyphus 不自写
- 每个子 Agent 返回后，自动按规则判断是否触发审查
- 不改已有 migration 文件
- 不改已有模型字段（除非明确需求）

---

## 参考文件

| 文件 | 路径 |
|------|------|
| 全局行为规则 | `~/.config/opencode/GLOBAL_RULES.md` |
| 复杂处理专员 Skill | `~/.config/opencode/skills/complex-task-specialist/SKILL.md` |
| 自动审查规则 | `~/.config/opencode/hooks/auto-review-rules.md` |
| 架构设计文档 | `C:\Users\chenshang\docs\plans\2026-06-06-summer-project-design.md` |
| Phase 1 实施计划 | `C:\Users\chenshang\docs\plans\2026-06-07-summer-phase1-plan.md` |
