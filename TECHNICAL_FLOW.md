# 技术方案（核心用户流程·事件驱动）

本文档梳理 Best Partners 项目从“用户提交需求”到“Agent 处理并前端展示”的端到端链路，聚焦事件、API 调用、数据形态与解析、持久化与渲染。作为联调与代码审查的落地说明。

## 0. 端口与启动（SSOT）
- Backend（FastAPI）：8080
- Frontend（Vite Dev Server）：5174
- Agent（LangGraph Dev）：2024
- 单一事实来源（.env）；前端代理读取 VITE_BACKEND_PORT；脚本 start_stack.sh 传递 VITE_DEV_PORT/VITE_BACKEND_PORT 并做健康检查。

## 1. 事件流概览
1) 事件 A：用户在首页提交需求（/api/v1/requirements/submit）
2) 事件 B：Workspace 首次加载，拉取全量状态（/api/v1/requirements/state）
3) 事件 C：版本目录更新，前端强制选中最新版本并渲染
4) 事件 D：用户在 Workspace 继续补充/勾选后发起跟进提交（/api/v1/requirements/submit）
5) 事件 E：前端轮询增量状态（/api/v1/requirements/status）+ 按需再取全量（/state）
6) 事件 F：后端将 Agent 回传状态落库（PostgreSQL），聚合并回传

---

## 2. 事件 A：用户在首页提交需求
- 前端页面：frontend/src/App.tsx 的 handleSubmit
- 请求：POST /api/v1/requirements/submit
- 请求体（示例）：
  {
    "user_id": "demo-user",
    "human_message": "帮我做个ppt",
    "timestamp": "2025-09-03T10:20:30.000Z",
    "model_params": { "provider": "openai", "base_url": "...", "model": "gpt-4o", ... }
  }
- 后端处理：
  - 接口定义：backend/app/routers/requirements.py /submit
  - 动作：
    1. 若缺省 model_params，尝试从数据库读取当前激活模型并注入（不阻断）。
    2. 若包含 thread_id，则从 DB 预载上下文作为 preload_state 传给 Agent（不阻断）。
    3. 转调 Agent /v1/submit（backend/app/services/agent_client.py）。
    4. 将 Agent 回传的完整状态做持久化（_persist_state）。
- 响应（关键字段）：
  {
    "thread_id": "...",
    "state_version": 1,
    "current_status": "clarifying",
    "requirements_document": { "version": "v1", "content": "...", "last_updated": "..." },
    "question_list": [ { "question_id": "...", "content": "...", "suggestion_options": [ {"option_id": "...", "content": "...", "selected": true} ] } ],
    "messages": [...],
    "multi_files": [...]
  }
- 前端动作：
  - 保存 thread_id/state_version 等并跳转到 /workspace?thread_id=...&state_version=...

## 3. 事件 B：Workspace 首次加载（全量状态）
- 前端页面：frontend/src/pages/Workspace.tsx
- 拉取：GET /api/v1/requirements/state?thread_id=... （已取消传入 state_version，取后端聚合的全量数据）
- 后端聚合逻辑：backend/app/routers/requirements.py /state
  - 完全由 PostgreSQL 聚合生成：
    - 向后兼容字段：requirements_document、question_list、messages、multi_files
    - 新增聚合字段：versions（字符串数组）、documents（[{version, content, last_updated, current_status}]）
  - state_version 取所有 version 的数字部分最大值（无则为 0）
- 前端解析与渲染：
  - versions：覆盖本地版本目录；强制选择最新版本（数字最大/列表最后一个）。
  - documents：根据 activeVersionId 渲染对应文档内容。
  - question_list：作为“当前版本问题清单”的基础模板，历史版本问题清单置为不可勾选（只读）。

## 4. 事件 C：版本目录更新
- 条件：后端 /state 返回的 versions 与本地不一致，或轮询后发现有新版本。
- 前端：
  - 更新 versions 状态并强制 activeVersionId 指向最新版本。
  - 渲染最新版本的文档内容与问题清单（可勾选）。
  - 历史版本的问题清单全部禁用（不提交）。

## 5. 事件 D：Workspace 跟进提交
- 前端入口：Workspace.tsx 中的 handleSubmitFollowup
- 人类消息组织：
  - 组合用户输入（自由文本）+ 当前版本下勾选的问题选项（仅当前版本）
  - 历史版本的选项不提交；文档内容以“当前页面展示内容”为准
- 请求：POST /api/v1/requirements/submit
- 请求体（示例）：
  {
    "user_id": "demo-user",
    "human_message": "\n【补充】...\n【当前版本选项】...",
    "thread_id": "...",
    "state_version": 3,
    "timestamp": "2025-09-03T10:25:00.000Z",
    "model_params": { ... }
  }
- 后端：
  - 透传到 Agent /v1/submit；
  - 将返回状态持久化（sessions/messages/questions/suggestion_options/requirements_documents/multi_file）。
- 前端：
  - applyStateData 应用返回状态；
  - scheduleNextPoll(thread_id, state_version) 开始轮询；
  - 清空本次输入框。

## 6. 事件 E：轮询与增量刷新
- 前端轮询：GET /api/v1/requirements/status?thread_id=...&state_version=当前值
  - 返回字段：
    { "thread_id": "...", "client_state_version": X, "current_state_version": Y, "has_update": true|false }
- 若 has_update 为 true：
  - 触发一次 GET /api/v1/requirements/state?thread_id=... 拉取全量并应用。
- 应用策略：
  - versions/documents 全量覆盖；activeVersionId 强制指向最新版本
  - question_list 以最新版本为可勾选；历史版本禁用

## 7. 数据持久化（后端）
- 落库位置：backend/app/routers/requirements.py 的 _persist_state
- 数据表（从 SQL 聚合/持久化逻辑可见）：
  - sessions(thread_id, current_status, updated_at)
  - messages(message_id, thread_id, role, content, timestamp, metadata)
  - questions(question_id, thread_id, content, created_at)
  - suggestion_options(option_id, question_id, content, selected)
  - requirements_documents(thread_id, version, content, created_at, current_status)
  - multi_file(file_id, thread_id, file_name, file_type, file_path, file_content, message_id, created_at)
- /state 的 SQL 一次性聚合上述表，返回完整前端需要的视图（含 versions/documents）。

## 8. Agent 交互（后端转调）
- 适配器：backend/app/services/agent_client.py
  - /v1/submit：映射字段（含 files/preload_state/model_params）并转发
  - /v1/poll：使用 client_state_version 参数名
  - /v1/state：按 thread_id 拉取
- AGENT_BASE_URL 由 start_stack.sh 注入，遵循 2024 端口（可被环境覆盖）。

## 9. 前端渲染要点
- Workspace：
  - 版本切换：始终指向最新版本；历史版本问题只读
  - 提交：仅提交当前版本勾选的选项与当前文档内容（显示即所见）
  - 轮询：状态更新后做一次全量 /state 应用，确保 versions/documents 一致性
- 首页 App：提交成功即跳转 Workspace，避免首页与 Workspace 两处并发轮询。

## 10. 异常与重试
- /submit 失败：提示错误，不进入轮询
- /status 超时/失败：指数退避重试（前端已有定时器策略，可在失败后延迟重试）
- /state 异常：保底展示现有缓存并提示用户刷新

## 11. 验收建议
- 后端健康：GET /api/v1/health 应为 200
- 提交→状态→全量：/submit → /status(has_update) → /state(versions/documents)
- Workspace：
  - 版本目录自动定位最新
  - 历史版本问题不可勾选
  - 提交仅包含当前版本的勾选项与当前文档内容

（完）