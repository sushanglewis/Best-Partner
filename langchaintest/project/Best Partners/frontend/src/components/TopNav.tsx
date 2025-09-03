import React from 'react'
import '../App.css'

export default function TopNav() {
  return (
    <header className="topbar">
      <nav className="nav">
        <a className="brand" href="/">Best Partner</a>
        <a href="/home">首页</a>
        <a href="/models">模型管理</a>
        <a href="/workspace">Workspace</a>
      </nav>
    </header>
  )
}