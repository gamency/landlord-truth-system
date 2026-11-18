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