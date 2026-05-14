-- ============================================================
-- 全球军事动态分析研判系统 - 初始数据库 Schema
-- Version: 1.0
-- Date: 2026-05-14
-- ============================================================

-- 国家/地区表
CREATE TABLE IF NOT EXISTS countries (
    country_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(3) UNIQUE NOT NULL,  -- ISO 3166-1 alpha-3
    country_name_zh VARCHAR(100) NOT NULL,     -- 中文名称
    country_name_en VARCHAR(100) NOT NULL,     -- 英文名称
    region VARCHAR(50),                        -- 所属地区
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 军种表
CREATE TABLE IF NOT EXISTS military_branches (
    branch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(country_id) ON DELETE CASCADE,
    branch_code VARCHAR(20) UNIQUE NOT NULL,   -- 如 PLA_Navy, US_Army
    branch_name_zh VARCHAR(100) NOT NULL,
    branch_name_en VARCHAR(100) NOT NULL,
    branch_type VARCHAR(20),                  -- army/navy/air_force/rocket_force/coast_guard/marines
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(country_id, branch_code)
);

-- 军事单位表（含自引用 parent_unit_id）
CREATE TABLE IF NOT EXISTS units (
    unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(country_id) ON DELETE CASCADE,
    branch_id UUID REFERENCES military_branches(branch_id) ON DELETE SET NULL,
    parent_unit_id UUID REFERENCES units(unit_id) ON DELETE SET NULL,  -- 自引用
    unit_code VARCHAR(50) UNIQUE NOT NULL,     -- 部队编号
    unit_name VARCHAR(200) NOT NULL,           -- 部队名称
    unit_level VARCHAR(20),                    -- 旅/团/营/连/排
    unit_type VARCHAR(50),                    -- 作战/支援/后勤
    is_active BOOLEAN DEFAULT TRUE,
    established_date DATE,
    dissolved_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 装备性能参数表
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(country_id) ON DELETE CASCADE,
    equipment_type VARCHAR(50) NOT NULL,       -- tank/aircraft/ship/submarine/missile/radar
    equipment_name VARCHAR(200) NOT NULL,
    model_code VARCHAR(100),
    manufacturer VARCHAR(200),
    unit_id UUID REFERENCES units(unit_id) ON DELETE SET NULL,  -- 所属单位
    specifications JSONB,                      -- 性能参数 (JSON)
    operational_status VARCHAR(20),          -- active/testing/reserve/retired
    inventory_count INTEGER DEFAULT 0,
    deployment_location VARCHAR(200),
    first_service_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 位置轨迹表
CREATE TABLE IF NOT EXISTS positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID REFERENCES units(unit_id) ON DELETE CASCADE,
    equipment_id UUID REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    position_type VARCHAR(20),                -- fixed/moving
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    altitude_m DECIMAL(10, 2),
    accuracy_m DECIMAL(10, 2),
    position_source VARCHAR(50),             -- satellite/ground_radar/manual
    reported_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180)
);

-- 情报记录表
CREATE TABLE IF NOT EXISTS intelligence (
    intel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(country_id) ON DELETE CASCADE,
    intel_type VARCHAR(50) NOT NULL,         -- movement/exercise/deployment/incident
    title VARCHAR(300) NOT NULL,
    content TEXT,
    source_reliability VARCHAR(10),           -- A/B/C/D
    credibility VARCHAR(10),                 -- confirmed/probable/possible/doubtful
    location_description VARCHAR(300),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    event_date DATE,
    obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预警记录表
CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(country_id) ON DELETE CASCADE,
    alert_level VARCHAR(20) NOT NULL,       -- red/orange/yellow/blue
    alert_type VARCHAR(50) NOT NULL,        -- invasion/air_threat/missile/other
    title VARCHAR(300) NOT NULL,
    description TEXT,
    source_intel_id UUID REFERENCES intelligence(intel_id) ON DELETE SET NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    affected_area VARCHAR(300),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180)
);

-- 系统设置表
CREATE TABLE IF NOT EXISTS settings (
    setting_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20),               -- string/number/boolean/json
    description VARCHAR(300),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX idx_units_country ON units(country_id);
CREATE INDEX idx_units_branch ON units(branch_id);
CREATE INDEX idx_units_parent ON units(parent_unit_id);
CREATE INDEX idx_equipment_country ON equipment(country_id);
CREATE INDEX idx_equipment_unit ON equipment(unit_id);
CREATE INDEX idx_positions_unit ON positions(unit_id);
CREATE INDEX idx_positions_equipment ON positions(equipment_id);
CREATE INDEX idx_positions_reported ON positions(reported_at);
CREATE INDEX idx_intel_country ON intelligence(country_id);
CREATE INDEX idx_intel_type ON intelligence(intel_type);
CREATE INDEX idx_intel_event_date ON intelligence(event_date);
CREATE INDEX idx_alerts_country ON alerts(country_id);
CREATE INDEX idx_alerts_level ON alerts(alert_level);
CREATE INDEX idx_alerts_active ON alerts(is_active);

-- ============================================================
-- 初始数据
-- ============================================================
INSERT INTO settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('system_version', '1.0.0', 'string', '系统版本', TRUE),
('data_retention_days', '365', 'number', '数据保留天数', TRUE),
('alert_check_interval_minutes', '5', 'number', '预警检查间隔(分钟)', TRUE);
