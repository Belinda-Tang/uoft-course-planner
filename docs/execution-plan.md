# 开发执行计划

## 阶段总览

```
阶段 0  ████████████  项目基础设施          [✅ 完成]
阶段 1  ████████████  HTML骨架+CSS主题      [✅ 完成]
阶段 2  ░░░░░░░░░░░░  课程数据层            [待执行]
阶段 3  ░░░░░░░░░░░░  单方案规划引擎        [待执行]
阶段 4  ░░░░░░░░░░░░  规则校验+Overlap检测  [待执行]
阶段 5  ░░░░░░░░░░░░  对比功能              [待执行]
阶段 6  ░░░░░░░░░░░░  收尾打磨              [待执行]
```

---

## 阶段 0：项目基础设施

**预计工作量**：一次性（当前执行中）

**交付物**：
- [x] 文件夹结构（docs/, dev-logs/, src/）
- [x] [CLAUDE.md](../CLAUDE.md) — AI 工作指引
- [x] [docs/requirements.md](./requirements.md) — 功能需求
- [x] [docs/technical-spec.md](./technical-spec.md) — 技术规范
- [x] [docs/design-spec.md](./design-spec.md) — 设计规范
- [x] [docs/execution-plan.md](./execution-plan.md) — 本文档
- [ ] [dev-logs/2026-06-05.md](../dev-logs/2026-06-05.md) — 首日日志

---

## 阶段 1：HTML 骨架 + CSS 主题

**依赖**：阶段 0 完成
**预计行数**：HTML ~200 行 + CSS ~300 行

**任务清单**：
- [ ] 创建 `src/index.html` 基础文件
- [ ] 编写 HTML 结构：
  - Header（标题 + Logo）
  - Plans Container（方案卡片容器）
  - Plan Card 模板（配置区 + 统计栏 + 学期网格 + Breadth 进度 + Overlap 警告）
  - Compare Container（对比视图容器）
  - Footer（说明文字）
- [ ] 编写 CSS：
  - CSS 变量定义
  - 全局 reset 和排版
  - 卡片组件样式
  - 学期网格样式
  - Breadth 进度条样式
  - 响应式媒体查询
- [ ] 填充占位示例数据（静态 HTML，硬编码一个方案）

**验证标准**：
- 浏览器打开 `src/index.html`，页面渲染正常
- 桌面端：卡片式布局完整
- 移动端（DevTools 切换）：布局自适应
- 无 JS 错误（控制台为空）

---

## 阶段 2：课程数据层

**依赖**：阶段 1 完成
**预计行数**：JS ~250 行

**任务清单**：
- [ ] 定义课程库对象 `COURSE_CATALOG`（~25 门课程）
  - CS 相关：CSC108, CSC110, CSC111, CSC207, CSC236, CSC263, CSC309, CSC311, CSC318, CSC343, CSC369, CSC373, CSC404, CSC413, CSC454
  - Math 相关：MAT135, MAT136, MAT137, MAT223, MAT224, MAT235, MAT237
  - Stats 相关：STA130, STA237, STA238, STA261, STA302, STA303, STA304, STA410
  - Econ 相关：ECO101, ECO102, ECO200, ECO202, ECO220, ECO301, ECO302, ECO401
- [ ] 定义广度类别常量 `BREADTH_CATEGORIES`
- [ ] 定义专业对象：
  - `PROGRAM_CS_SPECIALIST`（含 AI / Game Design / Web Dev 三个 Focus）
  - `PROGRAM_ECONOMICS_MAJOR`
  - `PROGRAM_STATISTICS_MAJOR`
  - `PROGRAM_MATH_MINOR`
  - `PROGRAM_DATA_SCIENCE_MINOR`
- [ ] 定义所有专业的索引 `PROGRAMS`
- [ ] 定义 Focus 索引 `FOCUS_OPTIONS`

**验证标准**：
- 在浏览器控制台执行 `console.log(COURSE_CATALOG)` 输出完整课程数据
- `Object.keys(PROGRAMS).length === 5`
- 每门课程的 fce、breadth、term 字段完整

---

## 阶段 3：单方案规划引擎

**依赖**：阶段 2 完成
**预计行数**：JS ~300 行

**任务清单**：
- [ ] 实现 `collectCourses(plan)` — 根据学年+专业收集课程
- [ ] 实现 `distributeSemesters(allCourses)` — 学期分配算法
- [ ] 实现 `computeBreadth(allCourses, standard)` — 广度计算
- [ ] 实现 `computeStats(allCourses)` — 学分统计
- [ ] 实现 `renderPlanCard(plan)` — 单方案卡片渲染
- [ ] 实现 `renderSemesterGrid(semesterPlan)` — 学期表格渲染
- [ ] 实现 `renderBreadthTracker(breadthStatus)` — 进度条渲染
- [ ] 实现 `renderCourseCard(course)` — 课程卡片（可展开）
- [ ] 绑定事件：学年/专业下拉框 change → 实时重新渲染
- [ ] 课程卡片点击展开/收起

**验证标准**：
- 选择 CS Specialist + 大一 → 显示 CSC110, CSC111, MAT137 等课程
- 选择 Economics Major + 大二 → 显示 ECO101/102 + ECO200/202/220
- 切换到不同 Focus → 课程列表对应变化
- 每学期课程数 ≤ 6（推荐 5）
- Breadth 进度条随课程变化

---

## 阶段 4：规则校验 + Overlap 检测

**依赖**：阶段 3 完成
**预计行数**：JS ~150 行

**任务清单**：
- [ ] 实现 `detectOverlap(plan)` — 重叠检测算法
- [ ] 实现 `renderOverlapWarning(overlap)` — 红色警告组件
- [ ] 实现 `checkSemesterLoad(semesterPlan)` — 学期负载检查
- [ ] 实现 `renderElectiveSlots(remainingFCE)` — 选修课占位卡片
- [ ] 将警告组件集成到 PlanCard 渲染中

**验证标准**：
- 选择 "Stats Major + Math Minor" → 检测共有课程，显示重叠 FCE
- 重叠 FCE > 最大允许值 → 红色警告框出现
- 学年切换后 Overlap 重新计算
- 学期超过 5 门 → 橙色警告标签
- 选修课缺口正确显示（如 "还需 8 门选修课"）

---

## 阶段 5：对比功能

**依赖**：阶段 4 完成
**预计行数**：JS ~200 行

**任务清单**：
- [ ] 实现多方案状态管理（添加/删除方案，最多 3 个，最少 1 个）
- [ ] 实现 `renderCompareView()` — 并排对比视图
- [ ] 对比维度：
  - 总课程数量对比
  - FCE 统计对比（已完成 / 剩余）
  - 学期课程数对比
  - Overlap 对比
  - Breadth 满足对比
- [ ] 实现方案独立配置（每个方案的学年/专业/Focuse 独立）
- [ ] 移动端 Tab 切换适配

**验证标准**：
- 添加方案 B → 页面出现第二个方案卡片
- 两个方案设置不同专业 → 各自独立渲染课程
- 对比视图正确显示差异
- 删除方案 → 最少保留 1 个
- 移动端 Tab 切换正常

---

## 阶段 6：收尾打磨

**依赖**：阶段 5 完成

**任务清单**：
- [ ] 课程卡片展开/收起动画（CSS transition）
- [ ] 删除确认弹窗
- [ ] 方案标签重命名功能
- [ ] 边界情况处理：
  - 空课程列表
  - 所有 Breadth 均为 0
  - 极端 overlap
- [ ] 性能检查（无内存泄漏、事件重复绑定）
- [ ] 全流程测试（3 种专业组合 × 4 个学年 × 2 种 Breadth 标准）

**验证标准**：
- 无 JS 报错
- 所有交互流畅（无卡顿）
- 移动端和桌面端均体验良好

---

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-06-05 | 初始版本，6 阶段开发计划 |
