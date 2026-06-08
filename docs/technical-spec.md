# 技术规范

## 技术栈

- **纯静态 Web**：HTML5 + CSS3 + ES6+ JavaScript
- **零构建工具**：无需 npm / webpack / vite
- **零运行时依赖**：不引入任何第三方 JS/CSS 库
- **可选 CDN**：Google Fonts（轻量字体）

---

## 数据架构

### 课程对象（Course）

```javascript
{
  code: "CSC110H1",           // 课程代码
  name: "计算机科学基础 I",     // 课程中文名
  description: "涵盖Python编程与算法基础", // 简短介绍
  fce: 0.5,                   // 学分值 (0.5=H课, 1.0=Y课)
  breadth: 4,                 // 广度类别编号 (1-5)
  term: "F"                   // 推荐学期 "F"|"S"|"Y" (Fall/Winter/Year)
}
```

### 专业对象（Program）

```javascript
{
  id: "cs_specialist",        // 唯一标识
  name: "计算机科学 Specialist", // 显示名
  type: "specialist",         // "specialist" | "major" | "minor"
  focusOptions: [             // Focus 选项（可选）
    {
      id: "ai",
      name: "人工智能方向",
      extraCourses: ["CSC311H1", "CSC413H1"] // 额外必修课程代码
    }
  ],
  prerequisites: ["CSC110H1", "CSC111H1"], // 大一进专业前置课
  requiredCourses: {          // 按推荐学年分组的必修课
    1: ["CSC110H1", "CSC111H1", "MAT137Y1"],
    2: ["CSC207H1", "CSC236H1", "CSC263H1"],
    3: ["CSC369H1", "CSC373H1"],
    4: ["CSC404H1"]
  }
}
```

### 广度类别

| 编号 | 名称 |
|------|------|
| 1 | 创意与文化表达 (Creative & Cultural) |
| 2 | 社会与行为科学 (Social & Behavioural) |
| 3 | 生命科学与环境 (Life Sciences & Environment) |
| 4 | 数学与物理科学 (Math & Physical Sciences) |
| 5 | 伦理与哲学 (Ethics & Philosophy) |

---

## 状态管理

### 全局状态

```javascript
const state = {
  plans: [
    {
      id: "plan_1",
      label: "方案 A",
      year: 1,                // 当前学年 (1-4)
      programs: [             // 选择的专业组合
        { programId: "cs_specialist", focusId: "ai" }
      ],
      breadthStandard: "A"    // "A" | "B"
    }
  ],
  activePlanIndex: 0          // 移动端当前显示的方案
}
```

### 计算属性（实时推导）

每个 Plan 对象的计算属性在渲染时动态生成：

| 属性 | 说明 |
|------|------|
| `allCourses` | 合并所有 Program 的课程（去重后） |
| `sharedCourses` | 被多个 Program 共用的课程列表 |
| `overlapFCE` | 重叠学分总和 |
| `maxOverlapFCE` | 允许的最大重叠 = (总FCE_A + 总FCE_B) − 12 |
| `semesterPlan` | 按学期分布的课程表 |
| `breadthStatus` | 5 个类别的覆盖 FCE |
| `totalFCE` | 已完成总学分 |
| `remainingFCE` | 还需选修学分 |
| `electiveSlots` | 选修课空位数 |

---

## 核心算法

### A1 — 课程收集

```
输入: plans[i] (学年 year, 专业列表 programs[])
输出: 课程列表 (去重), 共享课程列表

步骤:
1. 遍历 programs[] 中每个 program
2. 收集 prerequisites（仅当 year == 1）
3. 收集 requiredCourses 中 y <= year 的所有课程
4. 若有 focusId，收集对应 Focus 的 extraCourses
5. 合并所有课程，记录每门课属于哪些 program
6. 若一门课属于 ≥2 个 program，标记为共享课程
```

### A2 — Overlap 计算

```
输入: plans[i]
输出: { overlapFCE, maxOverlapFCE, isOver, sharedCourses }

步骤:
1. 如果 programs.length < 2，跳过（无重叠问题）
2. 计算每个 program 的总 FCE
3. maxOverlapFCE = (总FCE_A + 总FCE_B) − 12
4. overlapFCE = 共享课程的 FCE 之和
5. isOver = overlapFCE > maxOverlapFCE
```

### A3 — 学期分配

```
输入: allCourses, year
输出: semesterPlan = { "Y1F": [], "Y1W": [], "Y1S": [], ... }

步骤:
1. 创建 12+4 个学期的空数组
2. 对于有明确 term 的课程，放入对应学期
3. 对于 year-specific 但无 term 的课程，按 Fall/Winter 交替分配
4. 保持每学期 ≤ 5 门课（超出标警告）
5. Summer 学期默认为空
```

### A4 — Breadth 计算

```
输入: allCourses, standard ("A" | "B")
输出: { categories: [1..5], satisfied: boolean, missing: [] }

方案 A: 至少 4 个类别各 ≥ 1.0 FCE
方案 B: 至少 3 个类别各 ≥ 1.0 FCE + 其余 2 个类别各 ≥ 0.5 FCE
```

---

## 文件结构（src/index.html）

```
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>多伦多大学选课规划助手</title>
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style> /* CSS (~300行) */ </style>
</head>
<body>
  <!-- HTML 结构 (~200行) -->
  <script> /* JS (~800行) */ </script>
</body>
</html>
```

### JS 组织顺序

```
1. DATA 层 — 课程库、专业库、广度分类（纯数据，可替换）
2. STATE 层 — 全局状态初始化
3. COMPUTE 层 — 算法函数（纯函数，输入 state 输出计算结果）
4. RENDER 层 — DOM 渲染函数
5. EVENT 层 — 事件监听和绑定
6. INIT 层 — 启动应用
```
