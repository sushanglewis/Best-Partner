# Shang's Website

基于 React 18 + Material UI v5（Material 3 Design）打造的个人品牌展示站，数据结构化、主题可切换、响应式、科技感强，适合个人作品、简历、项目案例等展示。

## 目录结构

```
frontend/
  └── src/
      ├── App.jsx                # 应用入口
      ├── index.js              # React 挂载入口
      ├── data/config.js        # 结构化数据（个人信息、总结卡片、经历、项目等）
      ├── theme/theme.js        # MUI 主题配置
      ├── styles/global.css     # 全局样式
      ├── components/           # 全局组件（导航栏、底部栏、主题切换等）
      ├── pages/                # 各功能页面（LandingPage、HomePage、SummaryPage、ExperiencePage、ProjectsPage）
      └── ...
```

## 主要技术栈

- React 18
- Material UI v5（Material 3 Design）
- React Router v6
- Emotion（MUI 样式）

## 启动方式

```bash
cd frontend
npm install
npm start
```

默认开发端口：`http://localhost:3000` 或 `http://localhost:8080`

## 开发规范

- 组件、页面全部采用函数式组件
- 主题、配色、圆角、动效等全部通过 MUI 主题系统集中管理
- 数据全部结构化存储于 `src/data/config.js`
- 代码风格统一 Prettier + ESLint（airbnb/MUI 推荐）
- 支持明暗主题切换、响应式布局

## 数据结构说明

- 个人信息、总结卡片、工作经历、项目案例等全部结构化存储，便于自动化渲染与扩展
- 详见 `src/data/config.js`

## 页面说明

- **LandingPage**：动态首页，动画、行动呼吁、主题切换
- **HomePage**：欢迎语、导航、底部信息
- **SummaryPage**：个人愿景、总结卡片、行动呼吁
- **ExperiencePage**：工作经历卡片化展示
- **ProjectsPage**：项目案例卡片化展示，支持标签

## 主题与样式

- 完全 Material 3 Design 体系，支持明暗模式
- 全局样式见 `src/styles/global.css`

## 扩展建议

- 可集成动画（Framer Motion/Lottie/Three.js）、音效、社交账号、内容管理、API 对接等
- 支持多语言、内容动态化

---

如需更多定制开发或自动化扩展，请联系作者。
