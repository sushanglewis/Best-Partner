#!/usr/bin/env node

const { execSync } = require("child_process");

// 设置环境变量
process.env.FIGMA_ACCESS_TOKEN =
  "figd_ZJs_CfL5OTnPNRtbFSib28TjjkiGbhAIYeZG9t2B";

const command = process.argv[2];
const fileKey = process.argv[3];
const channel = process.argv[4] || "";
const channelArg = channel ? ` --channel=${channel}` : "";

if (!command) {
  console.log("🎨 Figma MCP 命令工具");
  console.log("");
  console.log("使用方法:");
  console.log(
    "  node scripts/figma-commands.js <command> [file_key] [channel]",
  );
  console.log("");
  console.log("可用命令:");
  console.log("  list-files     - 列出所有Figma文件");
  console.log("  get-file       - 获取文件信息 (需要file_key)");
  console.log("  get-styles     - 获取设计规范 (需要file_key)");
  console.log("  get-components - 获取组件信息 (需要file_key)");
  console.log("  export-images  - 导出图片 (需要file_key和node_ids)");
  console.log("");
  console.log("示例:");
  console.log("  node scripts/figma-commands.js list-files k6kxae42");
  console.log(
    "  node scripts/figma-commands.js get-file your_file_key k6kxae42",
  );
  process.exit(1);
}

try {
  let result;

  switch (command) {
    case "list-files":
      console.log("📁 获取Figma文件列表...");
      result = execSync(
        `npx cursor-talk-to-figma-mcp list-files${channelArg}`,
        {
          encoding: "utf8",
          env: process.env,
          timeout: 60000,
        },
      );
      break;

    case "get-file":
      if (!fileKey) {
        console.error("❌ 需要提供file_key");
        process.exit(1);
      }
      console.log(`📄 获取文件信息: ${fileKey}`);
      result = execSync(
        `npx cursor-talk-to-figma-mcp get-file ${fileKey}${channelArg}`,
        {
          encoding: "utf8",
          env: process.env,
          timeout: 15000,
        },
      );
      break;

    case "get-styles":
      if (!fileKey) {
        console.error("❌ 需要提供file_key");
        process.exit(1);
      }
      console.log(`🎨 获取设计规范: ${fileKey}`);
      result = execSync(
        `npx cursor-talk-to-figma-mcp get-styles ${fileKey}${channelArg}`,
        {
          encoding: "utf8",
          env: process.env,
          timeout: 15000,
        },
      );
      break;

    case "get-components":
      if (!fileKey) {
        console.error("❌ 需要提供file_key");
        process.exit(1);
      }
      console.log(`🧩 获取组件信息: ${fileKey}`);
      result = execSync(
        `npx cursor-talk-to-figma-mcp get-components ${fileKey}${channelArg}`,
        {
          encoding: "utf8",
          env: process.env,
          timeout: 15000,
        },
      );
      break;

    default:
      console.error(`❌ 未知命令: ${command}`);
      process.exit(1);
  }

  console.log("✅ 命令执行成功");
  console.log("📋 结果:");
  console.log(result);
} catch (error) {
  console.error("❌ 命令执行失败:", error.message);
  process.exit(1);
}
