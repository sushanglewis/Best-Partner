// Coze Chat SDK 智能体会话浮窗集成（自动生成）
// bot_id: 7525680393593372713
// 集成方式：页面加载时动态插入官方SDK script，加载完成后初始化WebChatClient
import React from "react";
import { NextUIProvider } from "@nextui-org/react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import NavigationBar from "./components/NavigationBar/NavigationBar.jsx";
import FooterBar from "./components/FooterBar/FooterBar.jsx";
import ThemeToggle from "./components/ThemeToggle/ThemeToggle.jsx";
import SocialIcons from "./components/SocialIcons/SocialIcons.jsx";
import LandingPage from "./pages/LandingPage/LandingPage.jsx";
import HomePage from "./pages/HomePage/HomePage.jsx";
import SummaryPage from "./pages/SummaryPage/SummaryPage.jsx";
import ExperiencePage from "./pages/ExperiencePage/ExperiencePage.jsx";
import ProjectsPage from "./pages/ProjectsPage/ProjectsPage.jsx";
import ChatWindowPage from "./pages/LandingPage/ChatWindowPage.jsx";

export default function App() {
  return (
    <NextUIProvider>
      <BrowserRouter>
        <NavigationBar />
        <ThemeToggle />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/summary" element={<SummaryPage />} />
          <Route path="/experience" element={<ExperiencePage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/chat" element={<ChatWindowPage />} />
        </Routes>
        <SocialIcons />
        <FooterBar />
      </BrowserRouter>
    </NextUIProvider>
  );
}
