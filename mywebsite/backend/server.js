/**
 * @file server.js
 * @description Express 后端服务入口，端口优先读取 process.env.PORT，默认 8081，自动输出启动信息，便于自动化与排查。
 */

const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();

// 中间件
app.use(cors());
app.use(express.json());

// 示例 API 路由（可根据实际需求扩展）
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", message: "Backend server is running." });
});

// 静态资源托管（如有前端构建产物，可启用）
// app.use(express.static(path.join(__dirname, '../frontend/build')));

// 端口设置
const PORT = process.env.PORT || 8081;

// 启动服务
app.listen(PORT, () => {
  console.log(`🚀 Backend server is running at http://localhost:${PORT}`);
});

module.exports = app;
