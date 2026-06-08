# 多伦多大学选课规划助手 — AI 工作指引

## 项目简介

本项目是一个**自包含的单文件 Web 应用**（`src/index.html`），帮助多伦多大学学生规划课程路径，核心特色是支持 2~3 个专业方案的并排对比。

- **目标用户**：不懂代码的学生（小白友好）
- **运行方式**：复制 `index.html` 到浏览器直接打开，无需服务器
- **技术栈**：纯 HTML + CSS + JavaScript（内联），零外部依赖

---

## 关键文件路径索引

| 文件 | 用途 |
|------|------|
| [CLAUDE.md](./CLAUDE.md) | 本文档，AI 工作指引 |
| [docs/requirements.md](./docs/requirements.md) | 功能需求文档 |
| [docs/technical-spec.md](./docs/technical-spec.md) | 技术规范（数据架构、算法） |
| [docs/design-spec.md](./docs/design-spec.md) | UI 设计规范（主题、布局、响应式） |
| [docs/execution-plan.md](./docs/execution-plan.md) | 分阶段开发执行计划 |
| [dev-logs/](./dev-logs/) | 每日开发日志（按日期命名 `YYYY-MM-DD.md`） |
| [src/index.html](./src/index.html) | 主产品文件（单文件应用） |

---

## 工作流程

### 每次对话开始时
1. 读取 `dev-logs/` 中最新的日志文件，了解当前进度
2. 读取 `docs/execution-plan.md`，确认当前应执行的阶段
3. 读取当前阶段的关联文档（requirements / technical-spec / design-spec）

### 开发过程
- **每次只做一个模块**，完成并验证后再进入下一个
- 修改 `src/index.html` 后，提醒用户在浏览器打开验证
- 每完成一个子任务，更新 `dev-logs/` 当日日志

### 每次对话结束时
- 更新 `dev-logs/` 当日日志，记录完成事项 + 待办 + 下一步
- 如果有架构或规范变更，同步更新 `docs/` 下的对应文档
- 标注当前阶段进度（如 "阶段 3 完成 60%"）

---

## 编码规范

### HTML
- 语义化标签（`<section>`, `<article>`, `<nav>` 等）
- 使用 `data-*` 属性标记 JS 交互元素
- 所有文本使用中文

### CSS
- 主题色：薄荷绿 `#A8E6CF`
- 辅助色：白色 `#FFFFFF`，深灰 `#333333`，警告红 `#E74C3C`
- 使用 CSS 变量定义颜色和间距
- Flexbox + Grid 布局
- 移动端断点：`768px`
- 类名使用 kebab-case
- 注释使用中文

### JavaScript
- 使用 ES6+ 语法（const/let、箭头函数、模板字符串、解构）
- 变量命名：camelCase
- 函数命名：动词开头（getXxx, renderXxx, computeXxx）
- 数据与逻辑分离：DATA 对象 → COMPUTE 函数 → RENDER 函数 → EVENT 绑定
- 注释使用中文
- 每个函数不超过 50 行
- 避免深层嵌套（最多 3 层）

---

## 增量开发约束

1. **单模块原则**：每次只实现一个功能模块，不跨模块修改
2. **先验证再前进**：每个模块完成后必须在浏览器中验证，确认无误再进入下一模块
3. **最小破坏**：修改已有代码时，只改必要部分，不改动已验证的稳定代码
4. **回退友好**：每完成一个模块，在 `dev-logs/` 中记录当前状态，方便出问题时定位

---

## 项目核心概念速查

### 学分规则
- H 课程（单学期）= **0.5 FCE**
- Y 课程（全年）= **1.0 FCE**
- 毕业要求 = **20 FCE** 总学分
- 每学期推荐 **5 门课**，最多 **6 门**

### 专业组合规则
- 允许组合：1 Specialist / 2 Majors / 1 Major + 2 Minors
- Overlap 规则：两个 Program 之间至少 **12 FCE 唯一** → 最大重叠 = (A+B总FCE) − 12

### Breadth 标准
- 方案 A：4 个类别各 ≥ 1.0 FCE
- 方案 B：3 个类别各 ≥ 1.0 FCE + 其余 2 个类别各 ≥ 0.5 FCE

### 学期结构
- 每年 Fall + Winter（共 8 个常规学期）
- Summer 可选（默认空，用于重修）
