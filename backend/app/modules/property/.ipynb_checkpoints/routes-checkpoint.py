from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.shared.db import db
from app.modules.property.models import Property, Room
from app.modules.property.schemas import CreatePropertyRequest, CreateRoomRequest

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

from app.modules.property.models import Meter
from app.modules.property.schemas import CreateMeterRequest

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

from app.modules.property.schemas import BatchCreatePropertyRequest

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

from datetime import datetime
from app.modules.property.models import Tenancy, BillDraft, OutboxEvent
from app.modules.property.schemas import SignTenancyRequest

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