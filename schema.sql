-- StreamBuy Multimodal Feature Store — Database Schema
-- Run against PostgreSQL: psql -d streambuy_features -f schema.sql

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(100),
    price NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processing_results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES processing_jobs(id),
    modality VARCHAR(50) NOT NULL,
    feature_vector FLOAT8[] NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_product_id ON processing_jobs(product_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_results_job_id ON processing_results(job_id);
CREATE INDEX IF NOT EXISTS idx_results_modality ON processing_results(modality);
