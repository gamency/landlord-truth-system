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