from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.shared.db import db
from app.modules.property.models import Property, Room, Meter, Tenancy, BillDraft, OutboxEvent, MeterReading, Payment, WriteOffRecord, ConfirmedBill
from app.modules.property.schemas import CreatePropertyRequest, CreateRoomRequest, CreateMeterRequest, BatchCreatePropertyRequest, SignTenancyRequest, RecordPaymentRequest, WriteOffRequest
from datetime import datetime
import random
import os
import base64
from werkzeug.utils import secure_filename
from openai import OpenAI
from app.config import settings

property_bp = Blueprint('property', __name__)

@property_bp.route('/properties', methods=['POST'])
def create_property():
    try:
        data = CreatePropertyRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    prop = Property(
        property_name=data.property_name,
        address=data.address,
        property_type=data.property_type,
    )
    db.session.add(prop)
    db.session.commit()

    return jsonify({
        "code": "OK",
        "data": {
            "property_id": str(prop.property_id),
            "property_name": prop.property_name,
        }
    }), 201


@property_bp.route('/properties/<property_id>/rooms', methods=['POST'])
def create_room(property_id):
    try:
        data = CreateRoomRequest(property_id=property_id, **request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    # 校验楼栋存在
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({"code": "NOT_FOUND_PROPERTY", "message": "楼栋不存在"}), 404

    room = Room(
        property_id=data.property_id,
        room_number=data.room_number,
        room_type=data.room_type,
        room_name=data.room_name,
        layout=data.layout,
    )
    db.session.add(room)
    db.session.commit()

    return jsonify({
        "code": "OK",
        "data": {
            "room_id": str(room.room_id),
            "room_number": room.room_number,
            "room_status": room.room_status,
        }
    }), 201


@property_bp.route('/properties', methods=['GET'])
def list_properties():
    props = db.session.query(Property).all()
    return jsonify({
        "code": "OK",
        "data": [
            {"property_id": str(p.property_id), "property_name": p.property_name,
             "address": p.address, "status": p.status}
            for p in props
        ]
    })

@property_bp.route('/properties/<property_id>/rooms', methods=['GET'])
def list_rooms(property_id):
    # 校验楼栋是否存在
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({"code": "NOT_FOUND_PROPERTY", "message": "楼栋不存在"}), 404

    # 查询该楼栋下的所有房间
    rooms = db.session.query(Room).filter_by(property_id=property_id).all()
    
    return jsonify({
        "code": "OK",
        "data": [
            {
                "room_id": str(r.room_id),
                "room_number": r.room_number,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "room_status": r.room_status
            }
            for r in rooms
        ]
    })

@property_bp.route('/rooms/<room_id>', methods=['GET'])
def get_room_detail(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"code": "NOT_FOUND_ROOM", "message": "房间不存在"}), 404
    
    # 查出该房间的所有表计
    meters = db.session.query(Meter).filter_by(room_id=room_id).all()
    
    return jsonify({
        "code": "OK",
        "data": {
            "room_id": str(room.room_id),
            "room_number": room.room_number,
            "room_status": room.room_status,
            "meters": [
                {
                    "meter_id": str(m.meter_id),
                    "meter_type": m.meter_type,
                    "meter_number": m.meter_number,
                    "current_reading": float(m.current_reading or 0)
                } for m in meters
            ]
        }
    })

@property_bp.route('/rooms/<room_id>/meters', methods=['POST'])
def bind_meter(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"code": "NOT_FOUND_ROOM", "message": "房间不存在"}), 404

    try:
        data = CreateMeterRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    # 检查该类型表计是否已绑定
    existing = db.session.query(Meter).filter_by(room_id=room_id, meter_type=data.meter_type).first()
    if existing:
        return jsonify({"code": "CONFLICT", "message": "该房间已绑定此类型表计"}), 409

    new_meter = Meter(
        room_id=room_id,
        property_id=room.property_id,
        meter_type=data.meter_type,
        meter_number=data.meter_number,
        initial_reading=data.initial_reading,
        current_reading=data.initial_reading
    )
    db.session.add(new_meter)
    db.session.commit()

    return jsonify({"code": "OK", "data": {"meter_id": str(new_meter.meter_id)}}), 201

@property_bp.route('/properties/batch', methods=['POST'])
def batch_create_property():
    try:
        data = BatchCreatePropertyRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    # 1. 创建楼栋
    prop = Property(
        property_name=data.property_name,
        address=data.address,
        property_type="SELF_BUILT",
    )
    db.session.add(prop)
    db.session.flush() # 先拿到 property_id

    # 2. 循环生成楼层和房间
    for floor in data.floors:
        for i in range(1, floor.room_count + 1):
            # 自动生成房间号：如 201, 202, 101
            room_num = f"{floor.floor_number}0{i}" if i < 10 else f"{floor.floor_number}{i}"
            
            room = Room(
                property_id=prop.property_id,
                room_number=room_num,
                room_name=f"{room_num}房" if floor.room_type == 'RENTAL' else f"{room_num}商铺",
                room_type=floor.room_type,
            )
            db.session.add(room)
            db.session.flush() # 拿到 room_id

            # 3. 自动绑定表计（表号按规则生成，房东无需手填）
            if floor.room_type in ['RENTAL', 'SHOP']:
                if floor.has_electric:
                    db.session.add(Meter(room_id=room.room_id, property_id=prop.property_id, meter_type='ELECTRIC', meter_number=f"E-{room_num}", initial_reading=0, current_reading=0))
                if floor.has_cold_water:
                    db.session.add(Meter(room_id=room.room_id, property_id=prop.property_id, meter_type='COLD_WATER', meter_number=f"W-{room_num}", initial_reading=0, current_reading=0))
                if floor.has_hot_water:
                    db.session.add(Meter(room_id=room.room_id, property_id=prop.property_id, meter_type='HOT_WATER', meter_number=f"H-{room_num}", initial_reading=0, current_reading=0))

    db.session.commit()
    return jsonify({"code": "OK", "data": {"property_id": str(prop.property_id)}}), 201

@property_bp.route('/rooms/<room_id>/sign', methods=['POST'])
def sign_tenancy(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"code": "NOT_FOUND_ROOM", "message": "房间不存在"}), 404
    if room.room_status == 'OCCUPIED':
        return jsonify({"code": "CONFLICT", "message": "房间已出租"}), 409

    try:
        data = SignTenancyRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    # 1. 创建租约
    tenancy = Tenancy(
        room_id=room_id,
        tenant_name=data.tenant_name,
        tenant_phone=data.tenant_phone,
        monthly_rent=data.monthly_rent,
        deposit_amount=data.deposit_amount,
        start_date=datetime.strptime(data.start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(data.end_date, '%Y-%m-%d').date()
    )
    db.session.add(tenancy)
    db.session.flush()

    # 2. 更新房间状态
    room.room_status = 'OCCUPIED'
    room.current_tenancy_id = tenancy.tenancy_id

    # 3. 生成首月账单草稿（理论应收 = 房租 + 押金）
    total_amount = data.monthly_rent + data.deposit_amount
    bill = BillDraft(
        tenancy_id=tenancy.tenancy_id,
        room_id=room_id,
        theoretical_amount=total_amount,
        actual_amount=total_amount
    )
    db.session.add(bill)

    # 4. 发布事件（写入 Outbox）
    event = OutboxEvent(
        event_type='TenancySigned',
        payload={
            "tenancy_id": str(tenancy.tenancy_id),
            "room_id": str(room_id),
            "tenant_name": data.tenant_name,
            "amount": str(total_amount)
        }
    )
    db.session.add(event)

    db.session.commit()

    return jsonify({"code": "OK", "message": "签约成功，账单草稿已生成"}), 201

# 查询所有待确认的草稿
@property_bp.route('/bills/drafts', methods=['GET'])
def list_bill_drafts():
    drafts = db.session.query(BillDraft).filter_by(status='DRAFT').all()
    # 为了前端好展示，顺便带出房间号
    result = []
    for d in drafts:
        room = db.session.get(Room, d.room_id)
        result.append({
            "draft_id": str(d.bill_draft_id),
            "room_number": room.room_number if room else "未知",
            "amount": float(d.actual_amount),
            "status": d.status
        })
    return jsonify({"code": "OK", "data": result})

# 确认账单草稿
@property_bp.route('/bills/drafts/<draft_id>/confirm', methods=['POST'])
def confirm_bill_draft(draft_id):
    draft = db.session.get(BillDraft, draft_id)
    if not draft or draft.status != 'DRAFT':
        return jsonify({"code": "ERROR", "message": "草稿不存在或已处理"}), 400

    # 1. 草稿状态改为已确认
    draft.status = 'CONFIRMED'

    # 2. 生成正式账单
    confirmed_bill = ConfirmedBill(
        source_draft_id=draft.bill_draft_id,
        tenancy_id=draft.tenancy_id,
        room_id=draft.room_id,
        amount=draft.actual_amount,
        remaining_amount=draft.actual_amount,
        status='CONFIRMED'
    )
    db.session.add(confirmed_bill)

    # 3. 发布事件
    event = OutboxEvent(
        event_type='BillConfirmed',
        payload={"bill_id": str(confirmed_bill.bill_id), "amount": str(confirmed_bill.amount)}
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({"code": "OK", "message": "账单已确认，等待发送"})

# 1. 查询所有已确认未结清的账单
@property_bp.route('/bills/confirmed', methods=['GET'])
def list_confirmed_bills():
    bills = db.session.query(ConfirmedBill).filter(ConfirmedBill.remaining_amount > 0).all()
    result = []
    for b in bills:
        room = db.session.get(Room, b.room_id)
        result.append({
            "bill_id": str(b.bill_id),
            "room_number": room.room_number if room else "未知",
            "amount": float(b.amount),
            "paid_amount": float(b.paid_amount or 0),
            "remaining_amount": float(b.remaining_amount),
            "status": b.status
        })
    return jsonify({"code": "OK", "data": result})

# 2. 录入收款
@property_bp.route('/payments', methods=['POST'])
def record_payment():
    try:
        data = RecordPaymentRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    payment = Payment(
        amount=data.amount,
        payer_name=data.payer_name,
        channel=data.channel,
        remaining_amount=data.amount
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({"code": "OK", "data": {"payment_id": str(payment.payment_id)}}), 201

# 3. 查询收款流水
@property_bp.route('/payments', methods=['GET'])
def list_payments():
    payments = db.session.query(Payment).order_by(Payment.created_at.desc()).all()
    return jsonify({
        "code": "OK",
        "data": [{
            "payment_id": str(p.payment_id),
            "amount": float(p.amount),
            "payer_name": p.payer_name,
            "channel": p.channel,
            "status": p.status,
            "remaining_amount": float(p.remaining_amount),
            "received_at": p.received_at.strftime('%Y-%m-%d %H:%M')
        } for p in payments]
    })

# 4. 核销（把收款扣到账单上）
@property_bp.route('/payments/<payment_id>/write-off', methods=['POST'])
def write_off_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment or payment.remaining_amount <= 0:
        return jsonify({"code": "ERROR", "message": "收款不存在或已全额核销"}), 400

    try:
        data = WriteOffRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"code": "VALIDATION_ERROR", "details": e.errors()}), 400

    bill = db.session.get(ConfirmedBill, data.bill_id)
    if not bill or bill.remaining_amount <= 0:
        return jsonify({"code": "ERROR", "message": "账单不存在或已结清"}), 400
    if data.amount > float(payment.remaining_amount):
        return jsonify({"code": "ERROR", "message": "核销金额超过收款余额"}), 400
    if data.amount > float(bill.remaining_amount):
        return jsonify({"code": "ERROR", "message": "核销金额超过账单欠款"}), 400

    # 扣减收款余额
    payment.remaining_amount = float(payment.remaining_amount) - data.amount
    if payment.remaining_amount == 0:
        payment.status = 'WRITTEN_OFF'

    # 扣减账单欠款
    bill.paid_amount = float(bill.paid_amount or 0) + data.amount
    bill.remaining_amount = float(bill.remaining_amount) - data.amount
    if bill.remaining_amount == 0:
        bill.status = 'PAID'

    # 记录核销流水
    record = WriteOffRecord(
        payment_id=payment.payment_id,
        bill_id=bill.bill_id,
        amount=data.amount
    )
    db.session.add(record)

    # 发布事件
    event = OutboxEvent(
        event_type='PaymentWrittenOff',
        payload={"payment_id": str(payment.payment_id), "bill_id": str(bill.bill_id), "amount": data.amount}
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({"code": "OK", "message": "核销成功"})

@property_bp.route('/bills/<bill_id>/pay', methods=['POST'])
def direct_pay_bill(bill_id):
    bill = db.session.get(ConfirmedBill, bill_id)
    if not bill or bill.remaining_amount <= 0:
        return jsonify({"code": "ERROR", "message": "账单不存在或已结清"}), 400

    data = request.get_json()
    amount = float(data.get('amount', 0))
    channel = data.get('channel', 'WECHAT')
    payer_name = data.get('payer_name', '未知')

    if amount <= 0 or amount > float(bill.remaining_amount):
        return jsonify({"code": "ERROR", "message": "收款金额不合法"}), 400

    # 1. 创建一条已直接核销的收款记录
    payment = Payment(
        amount=amount,
        payer_name=payer_name,
        channel=channel,
        remaining_amount=0, 
        status='WRITTEN_OFF'
    )
    db.session.add(payment)
    db.session.flush()

    # 2. 扣减账单欠款
    bill.paid_amount = float(bill.paid_amount or 0) + amount
    bill.remaining_amount = float(bill.remaining_amount) - amount
    if bill.remaining_amount == 0:
        bill.status = 'PAID'

    # 3. 生成核销记录
    record = WriteOffRecord(
        payment_id=payment.payment_id,
        bill_id=bill.bill_id,
        amount=amount
    )
    db.session.add(record)

    # 4. 发布事件
    db.session.add(OutboxEvent(
        event_type='BillPaid',
        payload={"bill_id": str(bill.bill_id), "amount": amount}
    ))
    
    db.session.commit()
    return jsonify({"code": "OK", "message": "收款成功"})

# 1. 模拟 AI 识别接口（接收房间，返回随机数字）
@property_bp.route('/rooms/<room_id>/ocr-mock', methods=['POST'])
def mock_ocr_reading(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"code": "NOT_FOUND", "message": "房间不存在"}), 404
        
    meter = db.session.query(Meter).filter_by(room_id=room_id, meter_type='ELECTRIC').first()
    if not meter:
        return jsonify({"code": "ERROR", "message": "该房间未绑定电表，无法抄表"}), 400

    # 模拟 AI 识别结果：80%概率正常，20%概率触发倒挂异常
    is_anomaly = random.random() < 0.2
    if is_anomaly:
        mock_value = float(meter.current_reading or 0) - 10 # 故意比上次小
        confidence = random.uniform(0.7, 0.85)
        status = 'ANOMALY'
    else:
        mock_value = float(meter.current_reading or 0) + random.uniform(10, 50)
        confidence = random.uniform(0.9, 0.99)
        status = 'SUCCESS'

    reading = MeterReading(
        room_id=room_id,
        meter_id=meter.meter_id,
        read_value=round(mock_value, 2),
        confidence=round(confidence, 2),
        image_url="/mock/path/img.jpg",
        status=status
    )
    db.session.add(reading)
    db.session.commit()

    return jsonify({
        "code": "OK",
        "data": {
            "reading_id": str(reading.reading_id),
            "room_number": room.room_number,
            "value": reading.read_value,
            "confidence": reading.confidence,
            "status": reading.status,
            "last_reading": float(meter.current_reading or 0)
        }
    })

# 2. 查询识别记录
@property_bp.route('/readings', methods=['GET'])
def list_readings():
    readings = db.session.query(MeterReading).order_by(MeterReading.created_at.desc()).limit(20).all()
    result = []
    for r in readings:
        room = db.session.get(Room, r.room_id)
        result.append({
            "reading_id": str(r.reading_id),
            "room_number": room.room_number if room else "未知",
            "value": float(r.read_value) if r.read_value else 0,
            "confidence": r.confidence,
            "status": r.status,
            "created_at": r.created_at.strftime('%H:%M:%S')
        })
    return jsonify({"code": "OK", "data": result})

# 3. 人工修正接口
@property_bp.route('/readings/<reading_id>/correct', methods=['POST'])
def correct_reading(reading_id):
    reading = db.session.get(MeterReading, reading_id)
    if not reading:
        return jsonify({"code": "NOT_FOUND", "message": "记录不存在"}), 404
        
    data = request.get_json()
    new_value = float(data.get('value'))
    
    # 修正原记录
    reading.read_value = new_value
    reading.status = 'MANUALLY_CORRECTED'
    
    # 更新电表当前读数
    meter = db.session.get(Meter, reading.meter_id)
    if meter:
        meter.current_reading = new_value
        
    db.session.commit()
    return jsonify({"code": "OK", "message": "修正成功"})

# ================= 真实的 AI OCR 视觉识别 =================
# 初始化视觉大模型客户端
vision_client = OpenAI(
    api_key=settings.AI_LLM_API_KEY,
    base_url=settings.AI_LLM_BASE_URL
)

@property_bp.route('/rooms/<room_id>/ocr-upload', methods=['POST'])
def real_ocr_reading(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"code": "NOT_FOUND", "message": "房间不存在"}), 404
        
    meter = db.session.query(Meter).filter_by(room_id=room_id, meter_type='ELECTRIC').first()
    if not meter:
        return jsonify({"code": "ERROR", "message": "该房间未绑定电表"}), 400

    if 'file' not in request.files:
        return jsonify({"code": "ERROR", "message": "未上传图片"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": "ERROR", "message": "图片文件名为空"}), 400

    # 1. 保存图片到本地
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)

    # 2. 转成 Base64 喂给多模态大模型
    with open(filepath, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        # 注意：这里的 model 需要填支持视觉的多模态 Endpoint
        # 如果你火山引擎只开了一个普通文本模型，这里可能会报错
        # 建议去火山引擎再开通一个 Doubao-vision 的 Endpoint ID，填入 settings.AI_VISION_MODEL
        vision_model = os.getenv("AI_VISION_MODEL", settings.AI_LLM_MODEL) 
        
        response = vision_client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "你是一个精准的电表读数识别专家。请仔细看这张图片，识别表盘上的数字读数。直接输出数字（保留两位小数），不要输出任何其他文字。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=20
        )
        
        ai_text = response.choices[0].message.content.strip()
        # 简单清理一下可能返回的非数字字符
        import re
        nums = re.findall(r'\d+\.?\d*', ai_text)
        if not nums:
            raise ValueError(f"未能识别出数字，模型返回：{ai_text}")
            
        mock_value = float(nums[0])

    except Exception as e:
        return jsonify({"code": "AI_ERROR", "message": f"AI识别失败: {str(e)}"}), 500

    # 3. 业务逻辑：判断是否倒挂，落库
    last_value = float(meter.current_reading or 0)
    status = 'SUCCESS'
    if mock_value < last_value:
        status = 'ANOMALY' # 读数倒挂

    # 模拟置信度（视觉大模型目前不直接返回置信度，我们按业务规则默认 98%）
    confidence = 0.98

    reading = MeterReading(
        room_id=room_id,
        meter_id=meter.meter_id,
        read_value=mock_value,
        confidence=confidence,
        image_url=f"/{filepath}",
        status=status
    )
    db.session.add(reading)
    db.session.commit()

    return jsonify({
        "code": "OK",
        "data": {
            "reading_id": str(reading.reading_id),
            "room_number": room.room_number,
            "value": reading.read_value,
            "confidence": reading.confidence,
            "status": reading.status,
            "last_reading": last_value
        }
    })