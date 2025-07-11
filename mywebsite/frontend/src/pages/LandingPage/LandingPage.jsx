import React from "react";
import { useNavigate } from "react-router-dom";
import Granim from "granim";
import { motion, AnimatePresence } from "framer-motion";
import ChatWindow from "./ChatWindow";
import TopBar from "../../components/TopBar/TopBar";

export default function LandingPage() {
  const navigate = useNavigate();
  const [chatOpen, setChatOpen] = React.useState(false);
  const [currentTextIndex, setCurrentTextIndex] = React.useState(0);

  // 轮播文本数组
  const carouselTexts = [
    {
      title: "你好",
      content: "Hi，欢迎来到我的Agent WebSite"
    },
    {
      title: "加入组织",
      content: "招募更多的独立开发者，实现非凡有趣的应用系统，共同进步，共同成功"
    },
    {
      title: "what i want",
      content: "用AI创造艺术，让世界变得更加有趣"
    },
    {
      title: "呼吁",
      content: "让我们一起做点真正有趣的事情"
    }
  ];

  // 自动轮播效果
  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTextIndex((prevIndex) => 
        prevIndex === carouselTexts.length - 1 ? 0 : prevIndex + 1
      );
    }, 5000); // 每5秒切换一次

    return () => clearInterval(timer);
  }, []);

  React.useEffect(() => {
    // 初始化 Granim 动画背景，使用官方默认配色
    const granimInstance = new Granim({
      element: "#granim-canvas",
      direction: "diagonal",
      isPausedWhenNotInView: true,
      states: {
        "default-state": {
          gradients: [
            ["#000814", "#001d3d", "#003566"], // 深空蓝 (宇宙深邃感)
            ["#1a0933", "#3d1765", "#7d3cff"], // 暗夜紫 (神秘科技感)
            ["#001219", "#005f73", "#0a9396"], // 深渊绿 (深海沉浸)
            ["#200122", "#3c1053", "#6a3093"], // 暗物质紫 (星云效果)
            ["#0d1926", "#1e3d59", "#2e5984"], // 午夜海军蓝 (现代质感)
            ["#0f0c29", "#302b63", "#24243e"], // 暗宇宙 (深邃星空)
            ["#2c003e", "#5d0c7b", "#9d4edd"], // 暗夜霓虹 (赛博朋克)
          ],
          transitionSpeed: 4000,
        },
      },
    });
    // 强制canvas永远在最底层
    const canvas = document.getElementById("granim-canvas");
    if (canvas) {
      canvas.style.zIndex = "0";
      canvas.style.pointerEvents = "none";
      canvas.style.position = "fixed";
    }
    // 动态加载 Coze SDK
    const script = document.createElement("script");
    script.src = "https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.1.0-beta.0/libs/cn/index.js";
    script.onload = () => {
      if (window.CozeWebSDK) {
        window.cozeWebSDK = new window.CozeWebSDK.WebChatClient({
          config: {
            botId: "7525680393593372713",
          },
          auth: {
            type: "token",
            token: "pat_2o6UiJ1m3eQsuWemzlHFBycmMBexSZf3VhpRHnqn2l2gz5mMLfcXtoa2ijy8Ad2I",
            onRefreshToken: () => Promise.resolve("pat_2o6UiJ1m3eQsuWemzlHFBycmMBexSZf3VhpRHnqn2l2gz5mMLfcXtoa2ijy8Ad2I")
          },
          user: { id: "user_" + Math.random().toString(36).slice(2, 12), nickname: "访客" },
          ui: {
            // 悬浮球（入口按钮）相关
            asstBtn: {
              isNeed: false, // 是否显示悬浮球（true显示，false隐藏）
              position: 'right', // 悬浮球位置（如支持，可选'right'/'left'/'bottom'等）
            },
            // 会话窗口相关
            width: 350, // 会话窗口宽度（单位px）
            height: 520, // 会话窗口高度（单位px，可选）
            placement: 'right', // 会话窗口弹出位置（如支持，可选'right'/'left'/'bottom'等）
            theme: 'dark', // 主题（可选'dark'/'light'等）
            backgroundColor: '#181C20', // 会话窗口背景色
            // 其他可选UI参数
            agentName: { isShow: false }, // 是否显示智能体名称
            icon: { isShow: false }, // 是否显示智能体头像
            minimizeBtn: { isShow: true }, // 是否显示最小化按钮
            closeBtn: { isShow: true }, // 是否显示关闭按钮
            inputPlaceholder: '请输入您的问题…', // 输入框占位符
            welcome: '欢迎使用Coze智能体', // 欢迎语
          },
        });
      }
    };
    document.body.appendChild(script);
    return () => {
      granimInstance.destroy();
      document.body.removeChild(script);
    };
  }, []);

  const cardStyle = {
    maxWidth: 520,
    padding: 40,
    marginBottom: 32,
    textAlign: "center",
    borderRadius: 20,
    background: "transparent",
    border: "none",
    boxShadow: "none",
    fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    color: "#161616",
    letterSpacing: 1,
    zIndex: 1,
  };
  const buttonStyle = {
    fontWeight: 800,
    fontSize: 36, // 调整为36px
    marginTop: 24,
    color: "#fff", // 白色填充
    WebkitTextStroke: "1.5px #fff",
    textStroke: "1.5px #fff",
    letterSpacing: 0.5,
    fontFamily:
      "'Inter', 'IBM Plex Sans', 'SF Pro Display', 'Roboto', 'Helvetica Neue', 'Arial', 'PingFang SC', 'HarmonyOS Sans SC', 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', 'sans-serif'",
    lineHeight: 1.15,
    textAlign: "left",
    border: "none",
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: "12px 36px",
    cursor: "pointer",
    transition: "transform 0.2s",
    zIndex: 1,
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "transparent",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 顶部导航栏 */}
      <TopBar />
      {/* Granim 动画背景canvas */}
      <canvas
        id="granim-canvas"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />
      {/* 强制隐藏 Coze 悬浮球相关元素 */}
      <style>{`
        .coze-webchat-launcher, .coze-webchat-btn, div[style*='z-index'] button {
          display: none !important;
        }
      `}</style>
      {/* 轮播内容区域 */}
      <div
        style={{
          ...cardStyle,
          maxWidth: 1440,
          marginTop: 108, // 顶部留出TopBar高度+间距
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          position: 'relative',
          minHeight: 'calc(100vh - 108px)', // 确保内容区域占满剩余高度
        }}
      >
        {/* 轮播标题 */}
        <div
          style={{
            fontWeight: 700,
            fontSize: 'clamp(1.5rem, 6vw, 3rem)', // 响应式字体，原为48px
            margin: "0 0 24px 0",
            color: "transparent",
            WebkitTextStroke: "1.5px #fff",
            textStroke: "1.5px #fff",
            letterSpacing: 2,
            fontFamily:
              "'Inter', 'IBM Plex Sans', 'SF Pro Display', 'Roboto', 'Helvetica Neue', 'Arial', 'PingFang SC', 'HarmonyOS Sans SC', 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', 'sans-serif'",
            lineHeight: 1.15,
            textAlign: "center",
            whiteSpace: "pre-line",
            background:
              "linear-gradient(120deg, rgba(255,255,255,0.7) 20%, rgba(255,255,255,0.2) 60%, rgba(255,255,255,0.5) 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            textShadow: "0 4px 24px rgba(255,255,255,0.25), 0 1px 0 #fff",
          }}
        >
          {carouselTexts[currentTextIndex].title}
        </div>
        {/* 轮播内容 */}
        <div
          style={{
            fontWeight: 700,
            fontSize: 'clamp(2.25rem, 9vw, 4.5rem)', // 响应式字体，原为72px
            margin: "0 0 48px 0",
            color: "transparent",
            WebkitTextStroke: "1.5px #fff",
            textStroke: "1.5px #fff",
            letterSpacing: 1,
            fontFamily:
              "'Inter', 'IBM Plex Sans', 'SF Pro Display', 'Roboto', 'Helvetica Neue', 'Arial', 'PingFang SC', 'HarmonyOS Sans SC', 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', 'sans-serif'",
            lineHeight: 1.2,
            textAlign: "justify",
            textAlignLast: "center",
            background:
              "linear-gradient(120deg, rgba(255,255,255,0.7) 20%, rgba(255,255,255,0.2) 60%, rgba(255,255,255,0.5) 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            textShadow: "0 4px 24px rgba(255,255,255,0.25), 0 1px 0 #fff",
          }}
        >
          {carouselTexts[currentTextIndex].content}
        </div>
      </div>
        {/* “开始与我会话”恢复为纯文字，样式与主标题一致但字号36px */}
        <div
          style={{
            fontWeight: 800,
            fontSize: 36,
            color: "transparent",
            WebkitTextStroke: "1.5px #fff",
            textStroke: "1.5px #fff",
            letterSpacing: 0.5,
            fontFamily:
              "'Inter', 'IBM Plex Sans', 'SF Pro Display', 'Roboto', 'Helvetica Neue', 'Arial', 'PingFang SC', 'HarmonyOS Sans SC', 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', 'sans-serif'",
            lineHeight: 1.15,
            textAlign: "center",
            background:
              "linear-gradient(120deg, rgba(255,255,255,0.7) 20%, rgba(255,255,255,0.2) 60%, rgba(255,255,255,0.5) 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            textShadow: "0 4px 24px rgba(255,255,255,0.25), 0 1px 0 #fff",
            filter: "none",
            cursor: "pointer",
            userSelect: "none",
            transition: "opacity 0.2s",
            opacity: 0.92,
            position: "absolute",
            bottom: "48px",
            left: "50%",
            transform: "translateX(-50%)",
          }}
          title="点击开始会话"
          onClick={() => {
            // 优先模拟点击coze悬浮球
            const launcher = document.querySelector('.coze-webchat-launcher, .coze-webchat-btn, [class*=launcher]');
            if (launcher) {
              launcher.click();
            } else if (window.cozeWebSDK && typeof window.cozeWebSDK.showChatBot === 'function') {
              window.cozeWebSDK.showChatBot();
            } else {
              alert('聊天入口未加载，请稍后重试');
            }
          }}
          onMouseOver={e => { e.currentTarget.style.opacity = 1; }}
          onMouseOut={e => { e.currentTarget.style.opacity = 0.92; }}
        >
          开始与我会话
        </div>
        {/* 页面底部按钮和代码块已移除，仅保留主内容 */}
    </div>
  );
}
