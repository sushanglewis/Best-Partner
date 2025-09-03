#!/usr/bin/env python3
"""
调试通义千问的完整输出内容
"""
import json
import requests


def debug_qwen_output():
    """调试通义千问输出"""
    
    # Agent 服务 URL
    agent_url = "http://127.0.0.1:2024"
    
    # 构造测试请求
    test_request = {
        "user_id": "test_user_debug",
        "human_message": "我想开发一个在线教育平台",
        "timestamp": "2024-09-01T10:00:00Z",
        "files": [],
        "thread_id": "debug_qwen_thread",
        "state_version": 0,
        "current_status": "clarifying",
        "model_params": {
            "provider": "dashscope",
            "model": "qwen-plus-latest",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    }
    
    print("=== 调试通义千问输出 ===")
    
    try:
        resp = requests.post(
            f"{agent_url}/v1/submit",
            json=test_request,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 200:
            response_data = resp.json()
            
            print("=== 完整响应数据 ===")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            print("\n=== 问题列表详细分析 ===")
            question_list = response_data.get('question_list', [])
            for i, question in enumerate(question_list, 1):
                print(f"\n问题 {i}:")
                print(f"  Raw data: {json.dumps(question, indent=4, ensure_ascii=False)}")
                
        else:
            print(f"请求失败: {resp.status_code}")
            print(f"错误响应: {resp.text}")
            
    except Exception as e:
        print(f"异常: {e}")


if __name__ == "__main__":
    debug_qwen_output()