import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.shared.db import db

class Property(db.Model):
    __tablename__ = 'property'
    #__table_args__ = {'schema': 'public'} # 暂时放public，以后按上下文分schema

    property_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.String(30), nullable=False) # SELF_BUILT, APARTMENT...
    parking_config = db.Column(JSONB, nullable=True)
    charging_station_config = db.Column(JSONB, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)

    rooms = db.relationship('Room', backref='property', lazy=True)

class Room(db.Model):
    __tablename__ = 'room'

    room_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('property.property_id'), nullable=False)
    floor_id = db.Column(UUID(as_uuid=True), nullable=True) # 先简化，不建单独的floor表
    room_number = db.Column(db.String(20), nullable=False)
    room_name = db.Column(db.String(50), nullable=True)
    room_type = db.Column(db.String(30), nullable=False) # RENTAL, SHOP...
    room_status = db.Column(db.String(20), nullable=False, default='VACANT') # VACANT, OCCUPIED...
    layout = db.Column(JSONB, nullable=True)
    water_pricing_mode = db.Column(db.String(20), nullable=True)
    water_pricing_config = db.Column(JSONB, nullable=True)
    current_tenancy_id = db.Column(UUID(as_uuid=True), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)

    meters = db.relationship('Meter', backref='room', lazy=True)

class Meter(db.Model):
    __tablename__ = 'meter'

    meter_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meter_type = db.Column(db.String(20), nullable=False) # ELECTRIC, COLD_WATER...
    meter_number = db.Column(db.String(50), nullable=False, unique=True)
    room_id = db.Column(UUID(as_uuid=True), db.ForeignKey('room.room_id'), nullable=True) # 总表可为空
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('property.property_id'), nullable=False)
    
    installed_at = db.Column(db.Date, nullable=True)
    initial_reading = db.Column(db.Numeric(14, 2), nullable=True)
    current_reading = db.Column(db.Numeric(14, 2), nullable=True)
    meter_status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)