import React, { useEffect, useMemo, useRef, useState } from 'react'
import TopNav from '../components/TopNav'
import '../App.css'

interface QuestionOption { option_id: string; content: string; selected?: boolean }
interface Question { question_id: string; content: string; suggestion_options?: QuestionOption[] }

interface DocumentItem { version: string; content: string; last_updated?: string; current_status?: string }

interface StateResponse {
  thread_id: string
  state_version: number
  current_status: string
  requirements_document?: { version?: string; content?: string; last_updated?: string }
  question_list: Question[]
  // 新增：后端聚合返回
  versions?: string[]
  documents?: DocumentItem[]
}

interface SubmitResponse extends StateResponse {}

type ModelConfig = { provider?: string; base_url?: string; model?: string; temperature?: number; max_tokens?: number; api_key?: string }

export default function Workspace() {
  const [threadId, setThreadId] = useState<string | null>(null)
  const [stateVersion, setStateVersion] = useState<number | null>(null)
  const [currentStatus, setCurrentStatus] = useState<string>('')

  const [versions, setVersions] = useState<string[]>([])
  const [activeVersionId, setActiveVersionId] = useState<string | null>(null)
  const [doc, setDoc] = useState<string>('')
  const [questions, setQuestions] = useState<Question[]>([])

  // 编辑器相关
  const [isEditing, setIsEditing] = useState(false)
  const [editorValue, setEditorValue] = useState('')
  const isDirtyRef = useRef(false)

  const [selectedByVersion, setSelectedByVersion] = useState<Record<string, Record<string, Set<string>>>>({})
  const [userText, setUserText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const pollTimer = useRef<number | null>(null)
  const mountedRef = useRef(true)

  const versionCacheRef = useRef<Record<string, { doc: string; questions: Question[] }>>({})

  const cols = useMemo(() => ({ left: '2fr', mid: '5fr', right: '3fr' }), [])

  function getCurrentModelFromStorage(): ModelConfig | null {
    try { const raw = localStorage.getItem('bp.current_model'); return raw ? JSON.parse(raw) as ModelConfig : null } catch { return null }
  }
  function getUserId() { return 'demo-user' }

  useEffect(() => { // cleanup
    mountedRef.current = true
    return () => { mountedRef.current = false; if (pollTimer.current) { window.clearTimeout(pollTimer.current); pollTimer.current = null } }
  }, [])

  // 解析 URL 参数，并立即拉取一次 /state（仅使用 thread_id）
  useEffect(() => {
    const usp = new URLSearchParams(window.location.search)
    const tid = usp.get('thread_id')
    const sv = usp.get('state_version')
    if (tid) setThreadId(tid)
    // 首次加载：无论是否带 state_version，都先用 thread_id 拉取一次当前状态用于回显
    if (tid) {
      ;(async () => {
        try {
          const sres = await fetch(`/api/v1/requirements/state?thread_id=${encodeURIComponent(tid)}`)
          if (sres.ok) {
            const sdata: StateResponse = await sres.json()
            if (!mountedRef.current) return
            applyStateData(sdata)
            // 若 URL 没有提供 state_version，则用返回值补全，以便后续轮询
            if (!sv && typeof sdata.state_version === 'number') setStateVersion(sdata.state_version)
          }
        } catch {}
      })()
    }
    if (sv && !Number.isNaN(Number(sv))) setStateVersion(Number(sv))
  }, [])

  useEffect(() => { if (threadId && stateVersion != null) scheduleNextPoll(threadId, stateVersion, 1500) }, [threadId, stateVersion])

  function scheduleNextPoll(tid: string, sv: number, delay = 5000) {
    if (!mountedRef.current) return
    if (pollTimer.current) window.clearTimeout(pollTimer.current)
    pollTimer.current = window.setTimeout(() => pollOnce(tid, sv), delay)
  }

  function chooseMaxVersion(list: string[]): string | null {
    if (!list || list.length === 0) return null
    const numeric = list.map(x => ({ x, n: Number(x) }))
    const allNum = numeric.every(({ n }) => !Number.isNaN(n))
    if (allNum) {
      return numeric.sort((a, b) => a.n - b.n)[numeric.length - 1].x
    }
    return [...list].sort()[list.length - 1]
  }

  const latestVersionId = useMemo(() => chooseMaxVersion(versions || []), [versions])

  function applyStateData(sdata: StateResponse) {
    setStateVersion(sdata.state_version)
    setCurrentStatus(sdata.current_status)

    // 使用聚合返回的版本/文档
    const aggVersions = sdata.versions && sdata.versions.length > 0 ? sdata.versions : undefined
    const aggDocs = sdata.documents && sdata.documents.length ? sdata.documents : undefined

    if (aggVersions) {
      setVersions(aggVersions)
      // 刷新缓存
      if (aggDocs) {
        const cache: Record<string, { doc: string; questions: Question[] }> = {}
        for (const d of aggDocs) {
          cache[d.version] = { doc: d.content, questions: sdata.question_list || [] }
        }
        versionCacheRef.current = { ...versionCacheRef.current, ...cache }
      }
      // 强制选中最新版本
      const newest = chooseMaxVersion(aggVersions)
      setActiveVersionId(newest || null)

      // 渲染最新版本对应内容
      const showVer = newest || (aggVersions.length ? aggVersions[aggVersions.length - 1] : null)
      const contentFromCache = showVer ? versionCacheRef.current[showVer]?.doc || '' : ''
      const qs = sdata.question_list || []
      setDoc(contentFromCache)
      setQuestions(qs)
      if (!isEditing || !isDirtyRef.current) setEditorValue(contentFromCache)
      return
    }

    // 兼容旧行为：仅从 requirements_document 渲染
    const v = sdata.requirements_document?.version ? String(sdata.requirements_document.version) : null
    const content = sdata.requirements_document?.content || ''
    const qs = sdata.question_list || []

    if (v) {
      versionCacheRef.current[v] = { doc: content, questions: qs }
      setVersions(prev => {
        const next = prev.includes(v) ? prev : [...prev, v]
        const maxV = chooseMaxVersion(next)
        // 强制选中最新版本
        setActiveVersionId(maxV)
        return next
      })
      setDoc(content)
      setQuestions(qs)
      if (!isEditing || !isDirtyRef.current) setEditorValue(content)
    } else {
      setDoc(content)
      setQuestions(qs)
      if (!isEditing || !isDirtyRef.current) setEditorValue(content)
    }
  }

  async function pollOnce(tid: string, sv: number) {
    try {
      const res = await fetch(`/api/v1/requirements/status?thread_id=${encodeURIComponent(tid)}&state_version=${encodeURIComponent(String(sv))}`)
      if (!res.ok) { scheduleNextPoll(tid, sv, 5000); return }
      const data = await res.json() as { has_update: boolean }
      if (data.has_update) {
        const sres = await fetch(`/api/v1/requirements/state?thread_id=${encodeURIComponent(tid)}`)
        if (sres.ok) {
          const sdata: StateResponse = await sres.json()
          if (!mountedRef.current) return
          applyStateData(sdata)
          scheduleNextPoll(tid, sdata.state_version, 5000)
          return
        }
      }
      scheduleNextPoll(tid, sv, 5000)
    } catch { scheduleNextPoll(tid, sv, 6000) }
  }

  function toggleOption(qid: string, oid: string) {
    // 仅允许在最新版本下选择；历史版本禁用
    if (!activeVersionId || activeVersionId !== latestVersionId) return
    setSelectedByVersion(prev => {
      const next = { ...prev }
      const vSel = { ...(next[activeVersionId] || {}) }
      const set = new Set(vSel[qid] || [])
      if (set.has(oid)) set.delete(oid); else set.add(oid)
      vSel[qid] = set
      next[activeVersionId] = vSel
      return next
    })
  }

  function buildHumanMessage() {
    const lines: string[] = []
    const currentVer = activeVersionId || latestVersionId || ''
    const currentDoc = (isEditing ? editorValue : doc) || ''
    // 包含当前页面需求文档内容
    lines.push(`需求文档(v${currentVer || '-'}):\n${currentDoc}`)

    const selectedMap = currentVer ? (selectedByVersion[currentVer] || {}) : {}
    for (const q of questions) {
      const chosen = selectedMap[q.question_id]
      if (chosen && chosen.size > 0) {
        const optionTexts = (q.suggestion_options || []).filter(o => chosen.has(o.option_id)).map(o => o.content)
        if (optionTexts.length > 0) {
          lines.push(`问题: ${q.content}\n选项: ${optionTexts.join(' / ')}`)
        }
      }
    }
    if (userText.trim()) lines.push(`补充: ${userText.trim()}`)
    return lines.join('\n\n')
  }

  async function handleSubmitFollowup() {
    if (!threadId || stateVersion == null) return
    const text = buildHumanMessage()
    if (!text) return
    setSubmitting(true)
    try {
      const model_param = getCurrentModelFromStorage()
      const payload: any = { user_id: getUserId(), human_message: text, thread_id: threadId, state_version: stateVersion, timestamp: new Date().toISOString() }
      if (model_param) payload.model_params = model_param
      const res = await fetch('/api/v1/requirements/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!res.ok) { console.error('提交失败', res.status); return }
      const data: SubmitResponse = await res.json()
      applyStateData(data)
      scheduleNextPoll(threadId, data.state_version, 1000)
      setUserText('')
    } catch (e) { console.error(e) } finally { setSubmitting(false) }
  }

  // 当选择版本变化时，从缓存渲染对应内容
  useEffect(() => {
    if (!activeVersionId) return
    const cached = versionCacheRef.current[activeVersionId]
    if (cached) {
      setDoc(cached.doc)
      setQuestions(cached.questions)
      if (!isEditing || !isDirtyRef.current) setEditorValue(cached.doc)
    }
  }, [activeVersionId])

  // 编辑器：监测是否有本地未保存修改
  useEffect(() => {
    isDirtyRef.current = editorValue !== doc
  }, [editorValue, doc])

  function handleCopy() {
    navigator.clipboard.writeText(editorValue).catch(() => {})
  }

  function handleDownload() {
    const blob = new Blob([editorValue], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const filename = activeVersionId ? `requirements_v${activeVersionId}.md` : 'requirements.md'
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <TopNav />
      <div className="columns" style={{ maxWidth: 1920, margin: '0 auto', padding: '0 16px', display: 'grid', gridTemplateColumns: `${cols.left} ${cols.mid} ${cols.right}`, gap: 16, alignItems: 'start' }}>
        <aside className="col left">
          <div className="card">
            <div className="card-title">版本目录 {typeof stateVersion === 'number' && <span className="pill" style={{ marginLeft: 8 }}>state v{stateVersion}</span>} {currentStatus && <span className="pill" style={{ marginLeft: 6 }}>{currentStatus}</span>}</div>
            <div className="card-body">
              {!threadId && <div>缺少 thread_id</div>}
              <ul className="list">
                {versions.map(v => (
                  <li key={v} className={v === activeVersionId ? 'active' : ''} onClick={() => setActiveVersionId(v)}>
                    <div>v{v}</div>
                  </li>
                ))}
                {versions.length === 0 && <li><div>暂无版本</div></li>}
              </ul>
            </div>
          </div>
        </aside>

        <main className="col mid">
          <div className="card">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <div>需求文档 {activeVersionId ? `(v${activeVersionId})` : ''}</div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {isEditing && isDirtyRef.current && <span className="pill warn">未保存的本地修改</span>}
                <button className="secondary" onClick={() => setIsEditing(v => !v)}>{isEditing ? '预览' : '编辑'}</button>
                {isEditing && <>
                  <button className="secondary" onClick={handleCopy}>复制内容</button>
                  <button className="secondary" onClick={handleDownload}>下载 .md</button>
                </>}
              </div>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {!isEditing && (
                <div className="pre-wrap" style={{ padding: 12, minHeight: 240 }}>{doc || '暂无内容'}</div>
              )}
              {isEditing && (
                <textarea
                  value={editorValue}
                  onChange={e => setEditorValue(e.target.value)}
                  style={{ width: '100%', minHeight: 320, border: 'none', outline: 'none', padding: 12, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}
                  placeholder="在此编辑需求文档..."
                />
              )}
            </div>
          </div>
        </main>

        <section className="col right">
          <div className="card">
            <div className="card-title">Best-Partner-assistant</div>
            <div className="card-body">
              {questions.length === 0 && <div>暂无问题</div>}
              {questions.map(q => (
                <div key={q.question_id} className="q-item">
                  <div className="q-text">{q.content}</div>
                  <ul className="q-options" style={{ listStyle: 'none', paddingLeft: 0, opacity: activeVersionId !== latestVersionId ? 0.6 : 1 }}>
                    {(q.suggestion_options || []).map(op => (
                      <li key={op.option_id}>
                        <label style={{ display: 'flex', gap: 6, alignItems: 'center', cursor: activeVersionId !== latestVersionId ? 'not-allowed' : 'pointer' }}>
                          <input
                            type="checkbox"
                            disabled={activeVersionId !== latestVersionId}
                            checked={!!(activeVersionId && selectedByVersion[activeVersionId]?.[q.question_id]?.has(op.option_id))}
                            onChange={() => toggleOption(q.question_id, op.option_id)}
                          />
                          <span>{op.content}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              <textarea value={userText} onChange={e => setUserText(e.target.value)} placeholder="在此补充你的想法..." style={{ width: '100%', height: 100, borderRadius: 12, border: '1px solid #e5e7eb', padding: 10, marginTop: 8 }} />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                <button className="go" onClick={handleSubmitFollowup} disabled={submitting || !threadId}>{submitting ? '提交中...' : '提交'}</button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}