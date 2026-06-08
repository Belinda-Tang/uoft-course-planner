# UI 设计规范

## 设计系统

### 色彩

| 用途 | 色值 | 说明 |
|------|------|------|
| 主色 | `#A8E6CF` | 薄荷绿，Header 背景、按钮、高亮 |
| 主色深 | `#7ECBA1` | 按钮 hover、选中状态 |
| 主色浅 | `#D4F4E4` | 卡片背景、输入框 |
| 背景 | `#FFFFFF` | 页面主背景 |
| 背景灰 | `#F8F9FA` | 次级背景、卡片间隔 |
| 文字主 | `#2D3436` | 标题、正文 |
| 文字次 | `#636E72` | 辅助文字、标签 |
| 成功绿 | `#27AE60` | Breadth 满足标签 |
| 警告橙 | `#F39C12` | 学期超载警告 |
| 错误红 | `#E74C3C` | Overlap 超限警告 |
| 边框 | `#DFE6E9` | 卡片边框、分割线 |

### CSS 变量定义

```css
:root {
  --color-primary: #A8E6CF;
  --color-primary-dark: #7ECBA1;
  --color-primary-light: #D4F4E4;
  --color-bg: #FFFFFF;
  --color-bg-secondary: #F8F9FA;
  --color-text: #2D3436;
  --color-text-secondary: #636E72;
  --color-success: #27AE60;
  --color-warning: #F39C12;
  --color-error: #E74C3C;
  --color-border: #DFE6E9;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.12);
  --font-main: 'Noto Sans SC', 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Consolas', monospace;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}
```

### 字体

- 主字体：Noto Sans SC（Google Fonts，中文友好）
- 等宽字体：JetBrains Mono（课程代码使用）
- 字号层级：12px / 14px / 16px / 20px / 24px

---

## 组件规范

### 卡片（Card）

```
┌──────────────────────────────┐
│  card-header (标题 + 操作)   │  ← 圆角顶
├──────────────────────────────┤
│                              │
│  card-body (主体内容)        │  ← padding: 16px
│                              │
└──────────────────────────────┘
  box-shadow: var(--shadow)
  border-radius: var(--radius)
  background: var(--color-bg)
```

### 课程卡片（Course Card）

```
┌──────────────────────────────────┐
│  CSC110H1  ·  0.5 FCE  ·  BR4   │  ← 默认显示：代码 + FCE + 广度标签
│  计算机科学基础 I                │
│  ▼ 点击展开                      │  ← 点击后显示介绍
│  "涵盖Python编程与算法基础..."   │
└──────────────────────────────────┘
  border-left: 4px solid var(--color-primary)
  cursor: pointer
```

### 学期表格（Semester Grid）

```
        Fall        Winter       Summer
Y1   [5门课卡片]  [4门课卡片]  [空/1门课]
Y2   [5门课卡片]  [5门课卡片]  [空]
Y3   [4门课卡片]  [5门课卡片]  [空]
Y4   [5门课卡片]  [3门课卡片]  [空]
```

### Breadth 进度条

```
BR1 ████████░░ 1.5/1.0 ✓
BR2 ████░░░░░░ 1.0/1.0 ✓
BR3 ██░░░░░░░░ 0.5/1.0 ✗ ← 未满足用灰色
BR4 ██████████ 2.5/1.0 ✓
BR5 ░░░░░░░░░░ 0.0/1.0 ✗
```

### 警告组件

```
┌──────────────────────────────────────┐
│  ⚠ Overlap 超限！                    │
│  当前重叠 5.0 FCE，最大允许 4.0 FCE  │
│  重叠课程：CSC110, MAT137, STA237    │
└──────────────────────────────────────┘
  background: #FDECEA
  border-left: 4px solid var(--color-error)
  color: var(--color-error)
```

---

## 响应式布局

### Desktop（>768px）

```
┌──────────────────────────────────────────────┐
│  Header                                       │
├──────────────────────────────────────────────┤
│  方案A  │  方案B  │  方案C  │  (Grid 3列)    │
│         │         │         │                │
│  对比视图（底部横跨全宽）                     │
└──────────────────────────────────────────────┘
```

### Mobile（≤768px）

```
┌─────────────────────┐
│  Header             │
├─────────────────────┤
│  [方案A] 方案B 方案C│  ← 顶部 Tab 切换
├─────────────────────┤
│                     │
│  当前方案全部内容    │  ← 单列堆叠
│                     │
├─────────────────────┤
│  [底部导航]         │
└─────────────────────┘
```

### 断点

| 断点 | 宽度 | 布局行为 |
|------|------|----------|
| Mobile | ≤ 768px | 单列堆叠，Tab 切换方案 |
| Tablet | 768px - 1024px | 2 列方案卡片 |
| Desktop | > 1024px | 2-3 列并排，对比视图展开 |

---

## 交互规范

| 元素 | 交互 | 反馈 |
|------|------|------|
| 下拉框 | 选择 | 立即更新关联区域 |
| 课程卡片 | 点击 | 展开/收起介绍（平滑过渡） |
| 方案 Tab | 点击 | 切换当前方案（移动端） |
| 添加方案 | 点击按钮 | 新建方案卡片（最多 3 个） |
| 删除方案 | 点击 ✕ | 确认后移除（最少 1 个） |
| 警告标签 | 始终可见 | 红色闪烁或静态（不自动消失） |
