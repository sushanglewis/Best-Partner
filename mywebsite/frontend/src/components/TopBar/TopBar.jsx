import React from "react";

const navItems = ["首页", "邀约", "业务垂询", "案例了解"];

export default function TopBar() {
  // 判断是否为移动端（屏幕宽度≤600px）
  const [isMobile, setIsMobile] = React.useState(false);
  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 600);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 按钮通用样式（响应式）
  const btnStyle = {
    background: "transparent",
    border: "none",
    color: "#fff",
    fontFamily:
      "'Inter', 'IBM Plex Sans', 'SF Pro Display', 'Roboto', 'Helvetica Neue', 'Arial', 'PingFang SC', 'HarmonyOS Sans SC', 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', 'sans-serif'",
    fontWeight: 500, // 加粗
    fontSize: isMobile ? 16 : 20,
    lineHeight: "60px",
    letterSpacing: 0.5,
    margin: isMobile ? "0 12px" : "0 32px",
    cursor: "pointer",
    transition: "opacity 0.2s, filter 0.2s",
    opacity: 0.85,
    filter: "none",
    borderRadius: 8,
    outline: "none",
    display: "block",
    minWidth: isMobile ? 72 : 0,
    padding: isMobile ? "2px 2px" : undefined,
  };

  return (
    <nav
      style={{
        width: "100%",
        height: 60,
        background: "transparent",
        border: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: isMobile ? "flex-start" : "center",
        position: "fixed",
        top: 0,
        left: 0,
        zIndex: 20,
        userSelect: "none",
        overflowX: isMobile ? "auto" : "visible",
        WebkitOverflowScrolling: isMobile ? "touch" : undefined,
        padding: isMobile ? "0 8px" : 0,
        boxSizing: "border-box",
      }}
    >
      {navItems.map((item) => (
        <button
          key={item}
          style={btnStyle}
          onMouseOver={e => { e.currentTarget.style.opacity = 1; e.currentTarget.style.filter = "drop-shadow(0 2px 8px #fff3)"; }}
          onMouseOut={e => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.filter = "none"; }}
          tabIndex={-1}
        >
          {item}
        </button>
      ))}
    </nav>
  );
} 