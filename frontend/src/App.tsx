import './App.css'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopNav from './components/TopNav'

// --- Types aligned with backend schemas ---
interface SubmitResponse {
  thread_id: string
  state_version: number
  current_status: string
  requirements_document?: { version?: string; content?: string; last_updated?: string }
  question_list: Array<{
    question_id: string
    content: string
    suggestion_options?: Array<{ option_id: string; content: string; selected?: boolean }>
  }>
  messages: Array<any>
  multi_files: Array<any>
}

interface PollResponse {
  thread_id: string
  client_state_version: number
  current_state_version: number
  has_update: boolean
}

interface StateResponse extends SubmitResponse {}

type ModelConfig = {
  provider?: string
  base_url?: string
  model?: string
  temperature?: number
  max_tokens?: number
  api_key?: string
}

export default function App() {
  const navigate = useNavigate()

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [threadId, setThreadId] = useState<string | null>(null)
  const [stateVersion, setStateVersion] = useState<number | null>(null)
  const [currentStatus, setCurrentStatus] = useState<string>('')
  const [doc, setDoc] = useState<SubmitResponse['requirements_document']>(undefined)
  const [questions, setQuestions] = useState<SubmitResponse['question_list']>([])

  const pollTimer = useRef<number | null>(null)
  const mountedRef = useRef(true)

  function getCurrentModelFromStorage(): ModelConfig | null {
    try {
      const raw = localStorage.getItem('bp.current_model')
      return raw ? (JSON.parse(raw) as ModelConfig) : null
    } catch {
      return null
    }
  }

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (pollTimer.current) {
        window.clearTimeout(pollTimer.current)
        pollTimer.current = null
      }
    }
  }, [])

  function scheduleNextPoll(tid: string, sv: number, delayMs = 1500) {
    if (!mountedRef.current) return
    if (pollTimer.current) window.clearTimeout(pollTimer.current)
    pollTimer.current = window.setTimeout(() => pollOnce(tid, sv), delayMs)
  }

  async function pollOnce(tid: string, sv: number) {
    try {
      const url = `/api/v1/requirements/status?thread_id=${encodeURIComponent(tid)}&state_version=${encodeURIComponent(String(sv))}`
      const res = await fetch(url)
      if (!res.ok) {
        // 后端/Agent 可能短暂 502，稍后重试
        scheduleNextPoll(tid, sv, 2000)
        return
      }
      const data: PollResponse = await res.json()
      if (data.has_update) {
        // 拉取完整新状态
        const sres = await fetch(`/api/v1/requirements/state?thread_id=${encodeURIComponent(tid)}`)
        if (sres.ok) {
          const sdata: StateResponse = await sres.json()
          if (!mountedRef.current) return
          setStateVersion(sdata.state_version)
          setCurrentStatus(sdata.current_status)
          setDoc(sdata.requirements_document)
          setQuestions(sdata.question_list || [])
          scheduleNextPoll(tid, sdata.state_version, 1500)
          return
        }
      }
      // 无更新或获取失败则继续按旧版本轮询
      scheduleNextPoll(tid, sv, 1500)
    } catch (_e) {
      // 网络/暂时错误，继续轻量重试
      scheduleNextPoll(tid, sv, 2000)
    }
  }

  async function handleSubmit() {
    setError(null)
    if (!input.trim()) {
      setError('请输入需求，例如：帮我做个ppt')
      return
    }
    setLoading(true)
    try {
      const model_param = getCurrentModelFromStorage()
      const payload: any = {
        user_id: 'demo-user',
        human_message: input,
        timestamp: new Date().toISOString(),
      }
      // 修正字段名为 model_params（与后端 Pydantic 模型一致）
      if (model_param) payload.model_params = model_param

      const res = await fetch('/api/v1/requirements/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`提交失败: ${res.status} ${text}`)
      }
      const data: SubmitResponse = await res.json()
      setThreadId(data.thread_id)
      setStateVersion(data.state_version)
      setCurrentStatus(data.current_status)
      setDoc(data.requirements_document)
      setQuestions(data.question_list || [])

      // 需求：提交成功后立即进入 Workspace 页面
      navigate(`/workspace?thread_id=${encodeURIComponent(data.thread_id)}&state_version=${encodeURIComponent(String(data.state_version))}`)
      return
      // 不再在首页继续轮询，避免重复实例
      // scheduleNextPoll(data.thread_id, data.state_version, 1000)
    } catch (e: any) {
      setError(e?.message || '提交失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <TopNav />

      <main className="hero">
        <div className="hero-content">
          <h1 className="title" style={{ marginBottom: 8 }}>Best Partner</h1>
          <p className="subtitle" style={{ marginBottom: 40 }}>让人人都用好AI</p>
          <div className="search">
            <input
              className="search-input"
              placeholder="帮我做个ppt"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !loading) handleSubmit()
              }}
              disabled={loading}
            />
            <button className="go" onClick={handleSubmit} disabled={loading}>
              {loading ? '提交中...' : 'GO'}
            </button>
          </div>

          {error && <div className="error-tip">{error}</div>}

          {(threadId || currentStatus || doc || (questions && questions.length > 0)) && (
            <section className="result">
              <div className="result-head">
                <div className="left">
                  {threadId && <span className="tid">thread: {threadId}</span>}
                  {typeof stateVersion === 'number' && <span className="sv">state v{stateVersion}</span>}
                  <span className="pill">{currentStatus || '进行中'}</span>
                </div>
                <div className="right">
                  <a href={`/workspace?thread_id=${encodeURIComponent(threadId || '')}&state_version=${typeof stateVersion === 'number' ? encodeURIComponent(String(stateVersion)) : ''}`}>在 Workspace 查看</a>
                </div>
              </div>

              {doc && (
                <div className="card">
                  <div className="card-title">当前需求文档{doc?.version ? `（v${doc.version}）` : ''}</div>
                  <div className="card-body pre-wrap">{doc?.content || '暂无内容'}</div>
                </div>
              )}

              {questions && questions.length > 0 && (
                <div className="card">
                  <div className="card-title">最新澄清问题</div>
                  <div className="card-body">
                    {questions.map((q) => (
                      <div key={q.question_id} className="q-item">
                        <div className="q-text">{q.content}</div>
                        {q.suggestion_options && q.suggestion_options.length > 0 && (
                          <ul className="q-options">
                            {q.suggestion_options.map((op) => (
                              <li key={op.option_id} className={op.selected ? 'selected' : ''}>
                                {op.content}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </main>
    </>
  )
}
