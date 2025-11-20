-- PV Test Automation Database Schema
-- PostgreSQL Initialization Script

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users and authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Admin', 'Engineer', 'Reviewer', 'Approver', 'Guest')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Test protocols
CREATE TABLE IF NOT EXISTS protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    description TEXT,
    applicable_to TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Equipment management
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(255),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    purchase_date DATE,
    status VARCHAR(50) DEFAULT 'Operational' CHECK (status IN ('Operational', 'Maintenance', 'Calibration Due', 'Out of Service')),
    location VARCHAR(100),
    specifications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Calibration records
CREATE TABLE IF NOT EXISTS calibrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    certificate_number VARCHAR(100) UNIQUE NOT NULL,
    calibration_date DATE NOT NULL,
    valid_until DATE NOT NULL,
    calibration_lab VARCHAR(255),
    traceability VARCHAR(100),
    certificate_file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Test records
CREATE TABLE IF NOT EXISTS tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id VARCHAR(50) UNIQUE NOT NULL,
    protocol_id UUID REFERENCES protocols(id),
    sample_id VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(255),
    module_type VARCHAR(100),
    rated_power DECIMAL(10, 2),
    num_cells INTEGER,
    sample_quantity INTEGER,
    test_engineer_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Under Review', 'Approved', 'Rejected')),
    priority VARCHAR(20) DEFAULT 'Normal' CHECK (priority IN ('Normal', 'High', 'Urgent')),
    start_date TIMESTAMP WITH TIME ZONE,
    completion_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Test results
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    test_name VARCHAR(255) NOT NULL,
    test_sequence INTEGER,
    result_value JSONB,
    pass_fail VARCHAR(10) CHECK (pass_fail IN ('PASS', 'FAIL', 'N/A')),
    measurement_date TIMESTAMP WITH TIME ZONE,
    measured_by_id UUID REFERENCES users(id),
    equipment_used UUID REFERENCES equipment(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Review workflow
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id),
    review_type VARCHAR(50) CHECK (review_type IN ('Technical Review', 'Approval', 'Revision Request')),
    decision VARCHAR(50) CHECK (decision IN ('Approved', 'Request Revision', 'Rejected', 'Hold')),
    comments TEXT,
    signature_hash VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    report_number VARCHAR(100) UNIQUE NOT NULL,
    format VARCHAR(20) CHECK (format IN ('PDF', 'Word', 'Excel', 'HTML', 'LaTeX', 'JSON', 'XML')),
    file_path TEXT,
    file_size_bytes BIGINT,
    generated_by_id UUID REFERENCES users(id),
    llm_generated BOOLEAN DEFAULT FALSE,
    llm_provider VARCHAR(50),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    description TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    data_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- File uploads
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    file_path TEXT,
    uploaded_by_id UUID REFERENCES users(id),
    processing_status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_tests_status ON tests(status);
CREATE INDEX idx_tests_test_id ON tests(test_id);
CREATE INDEX idx_equipment_equipment_id ON equipment(equipment_id);
CREATE INDEX idx_calibrations_valid_until ON calibrations(valid_until);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_reviews_test_id ON reviews(test_id);
CREATE INDEX idx_reports_test_id ON reports(test_id);

-- Insert default data
INSERT INTO protocols (protocol_code, name, version, description, applicable_to) VALUES
    ('IEC_61215', 'IEC 61215 - Terrestrial PV Modules - Design Qualification', '2021', 'Crystalline silicon terrestrial photovoltaic modules design qualification', 'Crystalline Silicon Modules'),
    ('IEC_61730', 'IEC 61730 - PV Module Safety Qualification', '2016', 'Photovoltaic module safety qualification', 'All PV Module Types'),
    ('IEC_61853', 'IEC 61853 - PV Module Performance Testing', '2018', 'Photovoltaic module performance testing and energy rating', 'All PV Module Types'),
    ('IEC_62716', 'IEC 62716 - Ammonia Corrosion Testing', '2013', 'PV modules - Ammonia corrosion testing', 'Modules for Agricultural/Industrial Environments'),
    ('IEC_61701', 'IEC 61701 - Salt Mist Corrosion Testing', '2020', 'PV modules - Salt mist corrosion testing', 'Modules for Coastal/Marine Environments'),
    ('IEC_62804', 'IEC 62804 - PID Testing', '2015', 'Potential-Induced Degradation testing', 'Crystalline Silicon Modules'),
    ('IEC_60904', 'IEC 60904 - PV Device Measurement', '2020', 'Photovoltaic devices - Measurement of current-voltage characteristics', 'Individual PV Devices and Modules'),
    ('IEC_62759', 'IEC 62759 - Transportation Testing', '2019', 'Transportation testing for photovoltaic modules', 'Packaged PV Modules')
ON CONFLICT (protocol_code) DO NOTHING;

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION)
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
    ('admin', 'admin@pvtesting.com', crypt('admin123', gen_salt('bf')), 'System Administrator', 'Admin')
ON CONFLICT (username) DO NOTHING;

COMMIT;
