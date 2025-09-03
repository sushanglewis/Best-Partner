#!/usr/bin/env python3
"""
通义千问 LLM 测试脚本

测试参数：
- base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
- model: qwen3-1.7b
- api_key: sk-82dd55c1a9974e6eb39265ff660721b8
"""

import json
import requests
import time

# Agent 服务地址
AGENT_URL = "http://127.0.0.1:2024"

# 通义千问配置
qwen_config = {
    "provider": "qwen",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3-1.7b",
    "api_key": "sk-82dd55c1a9974e6eb39265ff660721b8",
    "temperature": 0.3,
    "max_tokens": 1024
}

def test_agent_submit():
    """测试 Agent 的 /v1/submit 接口"""
    url = f"{AGENT_URL}/v1/submit"
    
    payload = {
        "user_id": "test_user_001",
        "human_message": "我想开发一个简单的在线商城系统，需要用户注册、商品展示、购物车和订单管理功能。",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_params": qwen_config
    }
    
    print(f"发送请求到 {url}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功！")
            print(f"Thread ID: {result.get('thread_id')}")
            print(f"State Version: {result.get('state_version')}")
            print(f"Current Status: {result.get('current_status')}")
            print(f"需求文档: {result.get('requirements_document', {}).get('content', 'N/A')}")
            print(f"问题数量: {len(result.get('question_list', []))}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误详情: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求异常: {e}")
        return False

def test_health():
    """测试 Agent 健康状态"""
    url = f"{AGENT_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Agent 服务健康")
            print(f"状态: {response.json()}")
            return True
        else:
            print(f"❌ Agent 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接 Agent 服务: {e}")
        return False

if __name__ == "__main__":
    print("=== 通义千问 LLM 测试 ===")
    print(f"Base URL: {qwen_config['base_url']}")
    print(f"Model: {qwen_config['model']}")
    print(f"API Key: {qwen_config['api_key'][:10]}...")
    print()
    
    # 1. 健康检查
    print("1. 检查 Agent 服务状态...")
    if not test_health():
        print("❌ Agent 服务不可用，退出测试")
        exit(1)
    
    print()
    
    # 2. 提交测试
    print("2. 测试通义千问 LLM 调用...")
    success = test_agent_submit()
    
    if success:
        print("\n🎉 通义千问测试成功！")
    else:
        print("\n💥 通义千问测试失败")
        exit(1)