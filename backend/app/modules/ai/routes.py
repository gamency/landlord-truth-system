import json
import time
from flask import Blueprint, request, Response, stream_with_context
from openai import OpenAI
from app.config import settings
from app.shared.db import db
from app.modules.property.models import ConfirmedBill, Room

ai_bp = Blueprint('ai', __name__)

# 初始化大模型客户端
client = OpenAI(
    api_key=settings.AI_LLM_API_KEY,
    base_url=settings.AI_LLM_BASE_URL
)

# 定义给大模型用的工具集 (Schema)
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_unpaid_bills",
            "description": "查询系统中所有未结清的账单和欠款",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]

# 本地实际执行查库的函数
def execute_query_bills():
    bills = db.session.query(ConfirmedBill).filter(ConfirmedBill.remaining_amount > 0).all()
    result = []
    for b in bills:
        room = db.session.get(Room, b.room_id)
        result.append({"room_number": room.room_number if room else "未知", "amount": float(b.remaining_amount)})
    return json.dumps(result, ensure_ascii=False)

@ai_bp.route('/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    def generate():
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的房东经营助手。回答要简洁、热情，称呼我为老板。如果需要查数据，请调用工具。"},
                {"role": "user", "content": user_message}
            ]
            
            # 第一阶段：请求大模型（判断是否需要调工具）
            response = client.chat.completions.create(
                model=settings.AI_LLM_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=False # 第一阶段不用流式，先判断意图
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                # 通知前端：Agent 正在调用工具
                yield f"data: {json.dumps({'event': 'trace', 'text': '🛠️ 识别到需要查询数据，正在调用系统工具...'})}\n\n"
                
                messages.append(response_message)
                
                # 本地执行工具
                for tool_call in tool_calls:
                    if tool_call.function.name == "query_unpaid_bills":
                        function_response = execute_query_bills()
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": function_response,
                        })
                
                yield f"data: {json.dumps({'event': 'trace', 'text': '✅ 数据获取成功，正在生成回答...'})}\n\n"
            
            # 第二阶段：将工具结果喂回大模型，开始流式输出
            stream = client.chat.completions.create(
                model=settings.AI_LLM_MODEL,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    text = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'event': 'message', 'text': text}, ensure_ascii=False)}\n\n"
                    
            yield f"data: {json.dumps({'event': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'message', 'text': f'\n[系统报错: {str(e)}]'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')