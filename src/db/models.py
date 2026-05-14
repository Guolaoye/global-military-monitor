"""ORM 模型（SQLAlchemy）"""
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Country(Base):
    __tablename__ = "countries"
    country_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(3), unique=True, nullable=False)  # ISO 3166-1 alpha-3
    name_zh = Column(String(100), nullable=False)
    name_en = Column(String(100))
    region = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class MilitaryBranch(Base):
    __tablename__ = "military_branches"
    branch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.country_id", ondelete="CASCADE"))
    code = Column(String(20), unique=True, nullable=False)
    name_zh = Column(String(100), nullable=False)
    name_en = Column(String(100))
    branch_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Unit(Base):
    __tablename__ = "units"
    unit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.country_id", ondelete="CASCADE"))
    branch_id = Column(UUID(as_uuid=True), ForeignKey("military_branches.branch_id", ondelete="SET NULL"))
    parent_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.unit_id", ondelete="SET NULL"))
    unit_code = Column(String(50), unique=True, nullable=False)
    unit_name = Column(String(200), nullable=False)
    unit_level = Column(String(20))
    unit_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    established_date = Column(DateTime)
    dissolved_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Equipment(Base):
    __tablename__ = "equipment"
    equipment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.country_id", ondelete="CASCADE"))
    equipment_type = Column(String(50), nullable=False)
    equipment_name = Column(String(200), nullable=False)
    model_code = Column(String(100))
    manufacturer = Column(String(200))
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.unit_id", ondelete="SET NULL"))
    specifications = Column(JSON)
    operational_status = Column(String(20))
    inventory_count = Column(Integer, default=0)
    deployment_location = Column(String(200))
    first_service_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = "positions"
    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.unit_id", ondelete="CASCADE"))
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.equipment_id", ondelete="CASCADE"))
    position_type = Column(String(20))  # fixed/moving
    latitude = Column(String(20))
    longitude = Column(String(20))
    altitude_m = Column(String(20))
    accuracy_m = Column(String(20))
    position_source = Column(String(50))
    reported_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Intelligence(Base):
    __tablename__ = "intelligence"
    intel_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.country_id", ondelete="CASCADE"))
    intel_type = Column(String(50), nullable=False)  # movement/exercise/deployment/incident
    title = Column(String(300), nullable=False)
    content = Column(Text)
    source_reliability = Column(String(10))  # A/B/C/D
    credibility = Column(String(10))  # confirmed/probable/possible/doubtful
    location_description = Column(String(300))
    latitude = Column(String(20))
    longitude = Column(String(20))
    event_date = Column(DateTime)
    obtained_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.country_id", ondelete="CASCADE"))
    alert_level = Column(String(20), nullable=False)  # red/orange/yellow/blue
    alert_type = Column(String(50), nullable=False)  # invasion/air_threat/missile/other
    title = Column(String(300), nullable=False)
    description = Column(Text)
    source_intel_id = Column(UUID(as_uuid=True), ForeignKey("intelligence.intel_id", ondelete="SET NULL"))
    latitude = Column(String(20))
    longitude = Column(String(20))
    affected_area = Column(String(300))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    setting_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(20))  # string/number/boolean/json
    description = Column(String(300))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
