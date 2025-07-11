import React, { useRef, useEffect, useState } from "react";
import axios from "axios";

const API_TOKEN =
  "pat_2o6UiJ1m3eQsuWemzlHFBycmMBexSZf3VhpRHnqn2l2gz5mMLfcXtoa2ijy8Ad2I";
const AGENT_ID = "7525680393593372713";
const API_ENDPOINT = "https://api.coze.cn/v3/chat";

function getUserId() {
  let uid = localStorage.getItem("coze_userid");
  if (!uid) {
    uid = "user_" + Math.random().toString(36).slice(2, 12);
    localStorage.setItem("coze_userid", uid);
  }
  return uid;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState([]); // {role: 'user'|'agent', content: string, time: string}
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // 滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // 首次加载拉取智能体欢迎语
  useEffect(() => {
    async function fetchWelcome() {
      console.log('[ChatWindow] useEffect fetchWelcome start');
      setLoading(true);
      setError("");
      try {
        console.log('[ChatWindow] axios.post welcome', API_ENDPOINT, AGENT_ID, getUserId());
        const res = await axios.post(
          API_ENDPOINT,
          {
            agent_id: AGENT_ID,
            user: getUserId(),
            content: "你好",
          },
          {
            headers: { Authorization: `Bearer ${API_TOKEN}` },
          },
        );
        console.log('[ChatWindow] welcome response', res);
        if (res.data && res.data.messages && res.data.messages.length > 0) {
          setMessages([
            {
              role: "agent",
              content: res.data.messages[0].content,
              time: new Date().toISOString(),
            },
          ]);
          setConversationId(res.data.conversation_id);
        }
      } catch (e) {
        console.error('[ChatWindow] welcome error', e);
        setError("智能体欢迎语获取失败");
      } finally {
        setLoading(false);
      }
    }
    fetchWelcome();
  }, []);

  // 发送消息
  async function sendMessage() {
    if (!input.trim()) return;
    console.log('[ChatWindow] sendMessage start', input);
    setLoading(true);
    setError("");
    const userMsg = {
      role: "user",
      content: input,
      time: new Date().toISOString(),
    };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    try {
      console.log('[ChatWindow] axios.post send', API_ENDPOINT, AGENT_ID, getUserId(), conversationId);
      const res = await axios.post(
        API_ENDPOINT,
        {
          agent_id: AGENT_ID,
          user: getUserId(),
          content: userMsg.content,
          conversation_id: conversationId,
        },
        {
          headers: { Authorization: `Bearer ${API_TOKEN}` },
        },
      );
      console.log('[ChatWindow] send response', res);
      if (res.data && res.data.messages && res.data.messages.length > 0) {
        setMessages((msgs) => [
          ...msgs,
          {
            role: "agent",
            content: res.data.messages[0].content,
            time: new Date().toISOString(),
          },
        ]);
        setConversationId(res.data.conversation_id);
      }
    } catch (e) {
      console.error('[ChatWindow] send error', e);
      setError("消息发送失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  function handleInputKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div
      className="flex flex-col items-center w-full max-w-2xl mx-auto mt-4 sm:mt-2 px-2 sm:px-0"
      style={{ height: "60vh", minHeight: 320, fontFamily: 'Inter, IBM Plex Sans, Arial, sans-serif' }}
    >
      <div
        className="flex-1 w-full border border-gray-200 rounded-3xl p-6 sm:p-3 flex flex-col bg-white shadow-2xl max-w-2xl mx-auto mt-4 sm:mt-2 px-2 sm:px-0"
        style={{ minHeight: 0, height: "75%" }}
      >
        <div className="flex-1 overflow-y-auto pr-2" style={{ minHeight: 0 }}>
          {/* loading欢迎语提示 */}
          {loading && messages.length === 0 && (
            <div className="w-full flex justify-center items-center h-full">
              <div className="text-primary-600 text-lg sm:text-base font-bold animate-pulse bg-primary-50 px-6 py-3 rounded-2xl shadow-lg">
                正在加载欢迎语...
              </div>
            </div>
          )}
          {/* 消息气泡区 */}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`w-full flex mb-2 sm:mb-1 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <textarea
                readOnly
                className={`resize-none rounded-2xl px-4 py-2 sm:px-2 sm:py-1 text-base sm:text-sm font-sans border-none outline-none shadow-lg transition ${msg.role === "user" ? "bg-primary-600 text-white text-right" : "bg-gray-100 text-gray-900 text-left"}`}
                value={msg.content}
                rows={1}
                style={{
                  maxWidth: "70%",
                  minWidth: "20%",
                  width: "100%",
                  boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                  fontWeight: msg.role === "user" ? 600 : 500,
                  wordBreak: "break-word",
                  fontSize: window.innerWidth < 640 ? "0.95rem" : undefined,
                }}
              />
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        {error && <div className="text-red-500 text-sm mt-2 sm:mt-1 font-medium">{error}</div>}
      </div>
      <div
        className="w-full flex items-end gap-2 sm:gap-1 mt-4 sm:mt-2 bg-gray-50 rounded-2xl shadow-lg p-4 sm:p-2"
        style={{ height: "25%" }}
      >
        <textarea
          className="flex-1 rounded-2xl px-4 py-2 sm:px-2 sm:py-1 text-base sm:text-sm font-sans border border-primary-200 bg-white text-gray-900 placeholder-gray-400 resize-none outline-none shadow-inner focus:ring-2 focus:ring-primary-400 transition"
          rows={window.innerWidth < 640 ? 1 : 2}
          placeholder="请输入你的问题..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleInputKeyDown}
          disabled={loading}
          style={{ fontSize: window.innerWidth < 640 ? "0.98rem" : "1.1rem", fontWeight: 500 }}
        />
        <button
          className="px-6 sm:px-3 py-2 sm:py-1 rounded-2xl border-none bg-primary-600 text-white font-bold text-lg sm:text-base shadow-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-300 transition disabled:opacity-60 disabled:cursor-not-allowed"
          onClick={sendMessage}
          disabled={loading}
          style={{ minWidth: window.innerWidth < 640 ? 64 : 96 }}
        >
          {loading ? "发送中..." : "发送"}
        </button>
      </div>
    </div>
  );
}
