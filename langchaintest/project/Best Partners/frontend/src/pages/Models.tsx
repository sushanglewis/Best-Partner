import React, { useEffect, useMemo, useState } from 'react'
import TopNav from '../components/TopNav'
import '../App.css'

type ModelItem = {
  id: number
  user_id: string
  provider: string
  base_url?: string
  model?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
  active?: boolean
  created_at?: string
}

type ModelConfig = {
  provider?: string
  base_url?: string
  model?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
}

export default function Models() {
  const [list, setList] = useState<ModelItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<ModelConfig>({ provider: '', base_url: '', model: '', api_key: '', temperature: 0.7, max_tokens: 4096 })

  const layout = useMemo(() => ({ container: { maxWidth: 1920, margin: '0 auto', padding: '0 16px' }, grid: { display: 'grid', gridTemplateColumns: '4fr 6fr', gap: 16 } }), [])

  function getUserId() {
    // 简化：与后端接口一致，要求存在 user_id。可以从业务登录态/本地存储获得。
    return 'demo-user'
  }

  async function loadList() {
    setLoading(true)
    setError(null)
    try {
      const userId = getUserId()
      const res = await fetch(`/api/v1/models/list?user_id=${encodeURIComponent(userId)}`)
      if (!res.ok) {
        const t = await res.text()
        throw new Error(`加载失败: ${res.status} ${t}`)
      }
      const data = await res.json()
      const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
      setList(items || [])
    } catch (e: any) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadList() }, [])

  async function testConnection() {
    try {
      // /api/v1/models/test 接口接收的就是 ModelConfig
      const res = await fetch('/api/v1/models/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      const ok = res.ok
      alert(ok ? '连接成功' : `连接失败: ${res.status}`)
    } catch (e) {
      alert('连接失败')
    }
  }

  async function saveConfig() {
    try {
      const body = { user_id: getUserId(), config: form }
      const res = await fetch('/api/v1/models/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!res.ok) throw new Error('保存失败')
      await loadList()
      alert('保存成功')
    } catch (e: any) {
      alert(e?.message || '保存失败')
    }
  }

  async function activate(id: number) {
    try {
      const body = { user_id: getUserId(), model_id: id }
      const res = await fetch('/api/v1/models/activate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!res.ok) throw new Error('设为当前失败')
      // 写入 localStorage 供 App.tsx 使用
      const item = list.find(x => x.id === id)
      if (item) {
        const store = { provider: item.provider, base_url: item.base_url, model: item.model, api_key: item.api_key, temperature: item.temperature, max_tokens: item.max_tokens }
        localStorage.setItem('bp_current_model', JSON.stringify(store))
      }
      await loadList()
      alert('已设为当前模型')
    } catch (e: any) {
      alert(e?.message || '设为当前失败')
    }
  }

  return (
    <>
      <TopNav />
      <div style={{ ...layout.container, ...layout.grid }}>
        {/* 左：表单 */}
        <div className="card">
          <div className="card-title">模型配置</div>
          <div className="card-body">
            <div className="form-row">
              <label>provider</label>
              <input value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} />
            </div>
            <div className="form-row">
              <label>base_url</label>
              <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
            </div>
            <div className="form-row">
              <label>model</label>
              <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            </div>
            <div className="form-row">
              <label>api_key</label>
              <input value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
            </div>
            <div className="form-row">
              <label>temperature</label>
              <input type="number" step="0.1" value={form.temperature ?? 0.7} onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })} />
            </div>
            <div className="form-row">
              <label>max_tokens</label>
              <input type="number" value={form.max_tokens ?? 4096} onChange={(e) => setForm({ ...form, max_tokens: Number(e.target.value) })} />
            </div>
          </div>
          <div className="card-foot" style={{ display: 'flex', gap: 12 }}>
            <button className="pill" onClick={testConnection}>连接测试</button>
            <button className="pill" onClick={saveConfig}>保存配置</button>
          </div>
        </div>

        {/* 右：列表 */}
        <div className="card">
          <div className="card-title">已保存模型 {loading ? '（加载中）' : ''}</div>
          <div className="card-body">
            {error && <div style={{ color: 'tomato', marginBottom: 8 }}>{error}</div>}
            {(!list || list.length === 0) && <div>暂无配置</div>}
            <ul className="list">
              {list.map(m => (
                <li key={m.id} className={m.active ? 'active' : ''} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.provider} · {m.model}</div>
                    <small style={{ color: '#666' }}>{m.base_url}</small>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {!m.active && <button className="pill" onClick={() => activate(m.id)}>设为当前</button>}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  )
}
