import json
import time
from flask import Blueprint, request, Response, jsonify, stream_with_context
from app.shared.db import db
from app.modules.property.models import ConfirmedBill, Room

ai_bp = Blueprint('ai', __name__)

def detect_intent(message: str):
    message = message.lower()
    if "账单" in message or "欠款" in message or "欠" in message:
        return "QUERY_BILLS"
    return "GENERAL_CHAT"

def tool_query_bills():
    bills = db.session.query(ConfirmedBill).filter(ConfirmedBill.remaining_amount > 0).all()
    result = []
    for b in bills:
        room = db.session.get(Room, b.room_id)
        result.append({"room": room.room_number if room else "未知", "amount": float(b.remaining_amount)})
    return result

@ai_bp.route('/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    message = data.get('message', '')
    
    def generate():
        # 1. 意图识别
        intent = detect_intent(message)
        yield f"data: {json.dumps({'event': 'trace', 'text': '🤖 正在分析您的意图...'})}\n\n"
        time.sleep(0.5)
        
        if intent == "QUERY_BILLS":
            yield f"data: {json.dumps({'event': 'trace', 'text': '🎯 识别到意图：查询未结清账单'})}\n\n"
            time.sleep(0.5)
            
            # 2. 调用 Tool
            yield f"data: {json.dumps({'event': 'trace', 'text': '🛠️ 正在调用系统工具: QueryBills...'})}\n\n"
            bills = tool_query_bills()
            time.sleep(0.5)
            
            # 3. 生成回答
            yield f"data: {json.dumps({'event': 'trace', 'text': '✅ 数据获取成功，正在生成回答...'})}\n\n"
            time.sleep(0.5)
            
            if not bills:
                answer = "太棒了老板！我刚才查了一下系统，目前所有房间的账单都已经结清了，没有任何欠款。"
            else:
                answer = "老板，我帮您查了一下，目前系统里有以下未结清的账单：\n"
                for b in bills:
                    answer += f"- **{b['room']}房**：欠款 **¥{b['amount']:.2f}**\n"
                answer += "\n需要我帮您生成催收话术发给租客吗？"
        else:
            answer = "老板您好！我是您的 AI 经营助手。您可以直接问我“谁还欠钱？”或者“这个月利润怎么样？”，我会立刻帮您去查。"

        # 逐字流式输出回答，模拟大模型打字机效果
        for char in answer:
            yield f"data: {json.dumps({'event': 'message', 'text': char}, ensure_ascii=False)}\n\n"
            time.sleep(0.02)
            
        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    # 核心修复：使用 stream_with_context 保持上下文
    return Response(stream_with_context(generate()), mimetype='text/event-stream')