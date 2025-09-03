#!/usr/bin/env python3
"""
测试优化后的prompt是否能让通义千问输出正确的JSON格式
"""
import json
import requests
import time


def test_qwen_optimized_prompt():
    """测试通义千问与优化后的prompt"""
    
    # Agent 服务 URL
    agent_url = "http://127.0.0.1:2024"
    
    # 1. 健康检查
    try:
        health_resp = requests.get(f"{agent_url}/health", timeout=10)
        print(f"Health check: {health_resp.status_code} - {health_resp.json()}")
        if health_resp.status_code != 200:
            raise Exception(f"Agent service not healthy: {health_resp.status_code}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # 2. 构造测试请求
    test_request = {
        "user_id": "test_user",
        "human_message": "我想开发一个在线教育平台",
        "timestamp": "2024-09-01T10:00:00Z",
        "files": [],
        "thread_id": "test_optimized_prompt_thread",
        "state_version": 0,
        "current_status": "clarifying",
        "model_params": {
            "provider": "dashscope",
            "model": "qwen-plus-latest",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    }
    
    print(f"\n=== 测试请求 ===")
    print(f"模型: {test_request['model_params']['model']}")
    print(f"用户消息: {test_request['human_message']}")
    
    # 3. 发送请求
    try:
        start_time = time.time()
        resp = requests.post(
            f"{agent_url}/v1/submit",
            json=test_request,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        print(f"\n=== 响应 ===")
        print(f"状态码: {resp.status_code}")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        
        if resp.status_code == 200:
            response_data = resp.json()
            print(f"线程ID: {response_data.get('thread_id')}")
            print(f"状态版本: {response_data.get('state_version')}")
            print(f"当前状态: {response_data.get('current_status')}")
            
            # 检查 question_list 格式
            question_list = response_data.get('question_list', [])
            print(f"\n=== 问题列表验证 ===")
            print(f"问题数量: {len(question_list)}")
            
            if len(question_list) != 3:
                print(f"❌ 问题数量不正确，期望3个，实际{len(question_list)}个")
                return False
            
            for i, question in enumerate(question_list, 1):
                print(f"\n问题 {i}:")
                
                # 验证必需字段
                required_fields = ['question_id', 'content', 'suggestion_options']
                for field in required_fields:
                    if field not in question:
                        print(f"❌ 缺少字段: {field}")
                        return False
                
                print(f"  question_id: {question.get('question_id')}")
                print(f"  content: {question.get('content')[:50]}...")
                
                # 验证选项
                options = question.get('suggestion_options', [])
                print(f"  选项数量: {len(options)}")
                
                if len(options) != 3:
                    print(f"❌ 选项数量不正确，期望3个，实际{len(options)}个")
                    return False
                
                for j, option in enumerate(options, 1):
                    if not all(key in option for key in ['option_id', 'content', 'selected']):
                        print(f"❌ 选项 {j} 缺少必需字段")
                        return False
                    
                    if not isinstance(option['selected'], bool):
                        print(f"❌ 选项 {j} 的 selected 不是布尔值: {type(option['selected'])}")
                        return False
                    
                    print(f"    选项 {j}: {option['option_id']} - {option['content'][:30]}... (selected: {option['selected']})")
            
            # 验证 requirements_document
            req_doc = response_data.get('requirements_document', {})
            print(f"\n=== 需求文档验证 ===")
            required_doc_fields = ['version', 'content', 'last_updated']
            for field in required_doc_fields:
                if field not in req_doc:
                    print(f"❌ requirements_document 缺少字段: {field}")
                    return False
            
            print(f"版本: {req_doc.get('version')}")
            print(f"更新日期: {req_doc.get('last_updated')}")
            print(f"内容长度: {len(req_doc.get('content', ''))}")
            
            print(f"\n✅ JSON格式验证通过！优化后的prompt成功修复了通义千问输出格式问题")
            return True
            
        else:
            print(f"❌ 请求失败: {resp.status_code}")
            try:
                error_detail = resp.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误响应体: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


if __name__ == "__main__":
    print("=== 测试优化后的prompt格式 ===")
    success = test_qwen_optimized_prompt()
    if success:
        print("\n🎉 测试成功！优化后的prompt能够让通义千问输出符合要求的JSON格式")
    else:
        print("\n⚠️  测试失败，可能需要考虑更换更强大的LLM模型")