import React from "react";

export default function ChatWindowPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <button
        style={{
          fontSize: 28,
          padding: "20px 60px",
          borderRadius: 16,
          background: "#6750A4",
          color: "#fff",
          fontWeight: 700,
          border: "none",
          boxShadow: "0 4px 24px rgba(103,80,164,0.15)",
          cursor: "pointer",
          letterSpacing: 2,
        }}
        onClick={() => alert('请在首页（LandingPage）使用右下角按钮与我对话')}
      >
        开启会话
      </button>
    </div>
  );
} 