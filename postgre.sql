-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL
);

-- Folders Table
CREATE TABLE folders (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    drive_type VARCHAR(50) NOT NULL,
    drive_id VARCHAR(255) NOT NULL,
    site_id VARCHAR(255) NOT NULL
);

-- Documents Table
CREATE TABLE documents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    label VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    file_name VARCHAR(255),
    source VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    created_date_time TIMESTAMP NOT NULL,
    last_modified_date_time TIMESTAMP NOT NULL,
    web_url TEXT NOT NULL,
    download_url TEXT NOT NULL,
    drive_id VARCHAR(255) NOT NULL,
    site_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    description TEXT,
    created_by VARCHAR(255) NOT NULL,
    last_modified_by VARCHAR(255) NOT NULL,
    parent_folder_id VARCHAR(255),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (last_modified_by) REFERENCES users(id),
    FOREIGN KEY (parent_folder_id) REFERENCES folders(id)
);

-- FileMetadata Table
CREATE TABLE file_metadata (
    document_id VARCHAR(255) PRIMARY KEY,
    mime_type VARCHAR(255) NOT NULL,
    quick_xor_hash VARCHAR(255) NOT NULL,
    shared_scope VARCHAR(50) NOT NULL,
    created_date_time TIMESTAMP NOT NULL,
    last_modified_date_time TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Versions Table
CREATE TABLE versions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    e_tag VARCHAR(255) NOT NULL,
    c_tag VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    version_number INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Sessions Table
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    file_count INTEGER NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    warnings INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Classifiers Table
CREATE TABLE classifiers (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_hierarchy BOOLEAN NOT NULL,
    parent_id VARCHAR(255),
    prompt TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES classifiers(id)
);

-- ClassifierData Table
CREATE TABLE classifier_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    classifier_id VARCHAR(255) NOT NULL,
    code VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    prompt TEXT,
    FOREIGN KEY (classifier_id) REFERENCES classifiers(id)
);

-- Enrichers Table
CREATE TABLE enrichers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    search_term TEXT NOT NULL,
    body TEXT NOT NULL,
    active BOOLEAN NOT NULL,
    value TEXT
);

-- BGSClassifications Table
CREATE TABLE bgs_classifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    code VARCHAR(255) NOT NULL,
    explanation TEXT NOT NULL,
    tooltip TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- UserEdits Table
CREATE TABLE user_edits (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    field VARCHAR(255) NOT NULL,
    original_value TEXT NOT NULL,
    edited_value TEXT NOT NULL,
    edited_by VARCHAR(255) NOT NULL,
    edited_at TIMESTAMP NOT NULL,
    reason TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (edited_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_document_name ON documents(name);
CREATE INDEX idx_document_created ON documents(created_date_time);



-- Begin transaction to ensure atomicity
BEGIN;

-- Insert User Data with explicit error if fails
INSERT INTO users (id, email, display_name)
VALUES ('354a020c-cf84-4e30-afd3-07ba0b07c4fc', 'tom@hoppa.ai', 'Tom Goldsmith')
ON CONFLICT (id) DO NOTHING;

-- Verify user exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM users WHERE id = '354a020c-cf84-4e30-afd3-07ba0b07c4fc'
    ) THEN
        RAISE EXCEPTION 'User with id 354a020c-cf84-4e30-afd3-07ba0b07c4fc not found in users table';
    END IF;
END $$;

-- Insert Folder Data
INSERT INTO folders (id, name, path, drive_type, drive_id, site_id)
VALUES (
    '01FCBACZKAABKJMBSJT5CJHMDH26OD3W33',
    'Borehole Records - Petersfield',
    '/drives/b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu/root:/Main/Sample Documents/Borehole Records - Petersfield',
    'documentLibrary',
    'b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu',
    '54aef708-d676-4c8d-83ff-d76803a4ddea'
)
ON CONFLICT (id) DO NOTHING;

-- Insert Document Data
INSERT INTO documents (
    id, name, label, size, file_name, source, type, created_date_time,
    last_modified_date_time, web_url, download_url, drive_id, site_id,
    status, description, created_by, last_modified_by, parent_folder_id
)
VALUES (
    '01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K',
    'BGS borehole 426100 (SU72SW51).pdf',
    'BGS borehole 426100 (SU72SW51).pdf',
    3040,
    NULL,
    'sharepoint',
    'application/pdf',
    '2024-12-17 10:31:25',
    '2024-12-17 10:31:25',
    'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%20426100%20(SU72SW51).pdf',
    'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=ad57b405-4826-4162-8ca7-b406103c6fca&Translate=false&tempauth=v1.eyJzaXRlaWQiOiI1NGFlZjcwOC1kNjc2LTRjOGQtODNmZi1kNzY4MDNhNGRkZWEiLCJhcHBfZGlzcGxheW5hbWUiOiJIb3BwYSIsImFwcGlkIjoiZmEyY2Y0YzUtZjM5ZC00Zjc1LWEzMjAtMDI5MWFkMmYxMGM1IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL2hvcHBhdGVjaG5vbG9naWVzLnNoYXJlcG9pbnQuY29tQGJhYWNjMGViLTA5MGYtNGZjOC05ZjczLWQ4YWY0ZGE5NzUwZCIsImV4cCI6IjE3NTA5NTA2NDkifQ.CkAKDGVudHJhX2NsYWltcxIwQ01paTljSUdFQUFhRm5CV05XWkRiVTVwVFZWSFpUTnlOMVEyVjNSbFFVRXFBQT09CjIKCmFjdG9yYXBwaWQSJDAwMDAwMDAzLTAwMDAtMDAwMC1jMDAwLTAwMDAwMDAwMDAwMAoKCgRzbmlkEgI2NBILCOy93JWpsZo-EAUaDTQwLjEyNi40MS4xNjIqLFhFaU9pZHNZU29tRUpBREtnRkhiRldockdBZ0J0c1lNQ3RDTkt6dGhVZVk9MJkBOAFCEKGr7AiWQADQLJpfTCAo47xKEGhhc2hlZHByb29mdG9rZW5SCFsia21zaSJdaiQwMDJlYjkwOS1mOTFmLWY0NGEtNWJjYy1jMDBkYmQ5NjU3YjFyKTBoLmZ8bWVtYmVyc2hpcHwxMDAzMjAwMzcyNzUwM2FkQGxpdmUuY29tegEyggESCevArLoPCchPEZ9z2K9NqXUNkgEDVG9tmgEJR29sZHNtaXRoogEMdG9tQGhvcHBhLmFpqgEQMTAwMzIwMDM3Mjc1MDNBRLIBgQFteWZpbGVzLnJlYWQgYWxsZmlsZXMucmVhZCBhbGxmaWxlcy53cml0ZSBhbGxzaXRlcy5yZWFkIHNlbGVjdGVkc2l0ZXMgQmFzaWNQcm9qZWN0QWxsLlJlYWQgQmFzaWNQcm9qZWN0QWxsLldyaXRlIGFsbHByb2ZpbGVzLnJlYWTIAQE.WJruvtm0fe0vZOngDiK5agUrDobTWQSRC0b7cm0qLH8&ApiVersion=2.0',
    'b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu',
    '54aef708-d676-4c8d-83ff-d76803a4ddea',
    'N/A',
    NULL,
    '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
    '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
    '01FCBACZKAABKJMBSJT5CJHMDH26OD3W33'
),
    (
        '01FCBACZSU72SW59',
        'BGS borehole 12709323 (SU72SW59).pdf',
        'BGS borehole 12709323 (SU72SW59).pdf',
        3040,
        NULL,
        'sharepoint',
        'application/pdf',
        '2024-12-17 10:31:25',
        '2024-12-17 10:31:25',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%2012709323%20(SU72SW59).pdf',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example1',
        'b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu',
        '54aef708-d676-4c8d-83ff-d76803a4ddea',
        'N/A',
        NULL,
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '01FCBACZKAABKJMBSJT5CJHMDH26OD3W33'
    ),
    (
        '01FCBACZSU72SE15',
        'BGS borehole 426030 (SU72SE15).pdf',
        'BGS borehole 426030 (SU72SE15).pdf',
        3040,
        NULL,
        'sharepoint',
        'application/pdf',
        '2024-12-17 10:31:25',
        '2024-12-17 10:31:25',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%20426030%20(SU72SE15).pdf',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example2',
        'b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu',
        '54aef708-d676-4c8d-83ff-d76803a4ddea',
        'N/A',
        NULL,
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '01FCBACZKAABKJMBSJT5CJHMDH26OD3W33'
    ),
    (
        '01FCBACZSU72SW60',
        'BGS borehole 15952134 (SU72SW60).pdf',
        'BGS borehole 15952134 (SU72SW60).pdf',
        3040,
        NULL,
        'sharepoint',
        'application/pdf',
        '2024-12-17 10:31:25',
        '2024-12-17 10:31:25',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%2015952134%20(SU72SW60).pdf',
        'https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example3',
        'b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu',
        '54aef708-d676-4c8d-83ff-d76803a4ddea',
        'N/A',
        NULL,
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '01FCBACZKAABKJMBSJT5CJHMDH26OD3W33'
    )
ON CONFLICT (id) DO NOTHING;

-- Insert File Metadata
INSERT INTO file_metadata (
    document_id, mime_type, quick_xor_hash, shared_scope,
    created_date_time, last_modified_date_time
)
VALUES (
    '01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K',
    'application/pdf',
    'yXrJBwDlOIJTPw9eEQO6o2UT8NE=',
    'users',
    '2024-12-17 10:31:25',
    '2024-12-17 10:31:25'
)
ON CONFLICT (document_id) DO NOTHING;

-- Insert Version Data
INSERT INTO versions (
    document_id, e_tag, c_tag, timestamp, version_number
)
VALUES (
    '01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K',
    '"{AD57B405-4826-4162-8CA7-B406103C6FCA},1"',
    '"c:{AD57B405-4826-4162-8CA7-B406103C6FCA},1"',
    '2024-12-17 10:31:25',
    1
)
ON CONFLICT DO NOTHING;

-- Insert Session Data
INSERT INTO sessions (
    session_id, session_name, created_at, created_by,
    file_count, completed_at, status, warnings, row_count
)
VALUES (
    'soft-mails-cry',
    'Engineering Design - Ground Investigation Records',
    '2024-11-09 15:28:55.609',
    '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
    52,
    NULL,
    'draft',
    0,
    0
)
ON CONFLICT (session_id) DO NOTHING;

-- Insert Classifier Data
INSERT INTO classifiers (
    id, name, is_hierarchy, parent_id, prompt, description
)
VALUES
    (
        'ISO1',
        'Project',
        FALSE,
        NULL,
        'Identify any keywords or codes related to project names, phases, specific locations, or team allocations.',
        'Identifies the project or area linked to this document.'
    ),
    (
        'ISO2',
        'Originator',
        FALSE,
        NULL,
        'Identify any organization names, initials, or references indicating authorship or originating party.',
        'Determines the organization originating this document.'
    ),
    (
        'ISO3',
        'Functional Breakdown',
        FALSE,
        NULL,
        'Identify terms pointing to business functions or domains, such as finance, risk, commercial, legal, or operations.',
        'Defines the document’s functional area, e.g., finance or legal.'
    ),
    (
        'ISO4',
        'Spatial Breakdown',
        FALSE,
        NULL,
        'Identify references to physical layouts, levels, specific locations, site planning, or building zones.',
        'Specifies the physical area, such as a site or floor plan.'
    ),
    (
        'ISO5',
        'Type',
        FALSE,
        NULL,
        'Identify document format types like technical, financial, or contractual documents.',
        'Identifies the document type or format.'
    ),
    (
        'ISO6',
        'Discipline',
        FALSE,
        NULL,
        'Identify terms related to professional disciplines, such as engineering, architecture, or geology.',
        'Identifies the professional discipline associated with the document.'
    )
ON CONFLICT (id) DO NOTHING;

-- Insert Classifier Data Items
INSERT INTO classifier_data (
    classifier_id, code, description, prompt
)
VALUES
    ('ISO1', 'XXXV', 'Non-specific to project', ''),
    ('ISO1', 'HOPPA', 'Hoppa Technologies Limited', ''),
    ('ISO1', 'EHCRA', 'East Hampshire Petersfield Climate Resilience Audit & Geological Assessments', NULL),
    ('ISO2', 'HOP', 'Hoppa Technologies', 'Locate mentions of ''Hoppa Technologies'' or shortened references.'),
    ('ISO2', 'SER', 'Generic Services Provider; unspecified', 'Identify mentions of generic terms like ''service provider'', ''contractor'', or ''subcontractor''.'),
    ('ISO2', 'CLN', 'Generic Client Organisation; unspecified', 'Search for generic client-related terms like ''client'', ''customer'', ''organization''.'),
    ('ISO2', 'BGS', 'British Geological Survey', NULL),
    ('ISO3', 'ZZ', 'Applies to all functional areas', 'Confirm if applicable across all functions or departments.'),
    ('ISO3', 'XX', 'Non-specific to functional area', 'Check for non-functional or general terms, indicating broad relevance.'),
    ('ISO3', 'FN', 'Financial, commercial, risk', 'Identify any references to financial terms, economic analysis, risk management, or corporate finance.'),
    ('ISO3', 'LG', 'Legal, insurance, liability', 'Locate mentions of legal compliance, contracts, liability, or regulatory terms.'),
    ('ISO3', 'VG', 'Surveys; geotechnical, environmental, other', NULL),
    ('ISO3', 'HS', 'Health and Safety', NULL),
    ('ISO3', 'TP', 'Town, infrastructure planning', NULL),
    ('ISO3', 'ED', 'Engineering', NULL),
    ('ISO3', 'AC', 'Approvals & consents', NULL),
    ('ISO4', 'ZZ', 'Relevant to all physical areas', 'Confirm if relevant across all physical sites, levels, or sections.'),
    ('ISO4', 'XX', 'Non-specific to physical areas', 'Identify terms showing no specific physical location or layout.'),
    ('ISO4', 'SP', 'Site Plan; layouts', 'Look for terms related to site-wide layouts, zoning, or external areas.'),
    ('ISO4', 'FP', 'Floor Plan; layouts', 'Identify mentions of floor plans, interior layouts, or vertical arrangement across floors.'),
    ('ISO5', 'ZZ', 'Applies to all document types', 'Confirm if applicable across all document formats.'),
    ('ISO5', 'XX', 'Non-specific to document type', 'Identify terms showing no specific document format.'),
    ('ISO5', 'CN', 'Contractual', 'Locate terms related to contracts, agreements, or legal obligations.'),
    ('ISO5', 'FN', 'Financial', 'Identify references to financial data, budgets, or costings.'),
    ('ISO5', 'TC', 'Technical; reports, surveys', 'Look for technical terms related to reports, surveys, or engineering.'),
    ('ISO5', 'LG', 'Legal', NULL),
    ('ISO6', 'ZZ', 'All disciplines', 'Confirm if relevant across all professional disciplines.'),
    ('ISO6', 'XX', 'Non-specific to discipline', 'Identify terms showing no specific professional discipline.'),
    ('ISO6', 'GE', 'Geology, geotechnical', 'Locate terms related to geological surveys, geotechnical engineering, or soil analysis.'),
    ('ISO6', 'CV', 'Civil', NULL),
    ('ISO6', 'AR', 'Architecture', NULL)
ON CONFLICT DO NOTHING;

-- Insert Enricher Data
INSERT INTO enrichers (
    name, search_term, body, active, value
)
VALUES
    (
        'Client',
        'client',
        'Extract name(s) of client(s) mentioned in the document.',
        TRUE,
        NULL
    ),
    (
        'Client Contact',
        'client contact',
        'Extract details of any client contacts mentioned in the document, including names, roles, or contact details.',
        TRUE,
        NULL
    ),
    (
        'Contractor',
        'contractor',
        'Extract name(s) of contractor(s) mentioned in the document.',
        TRUE,
        NULL
    ),
    (
        'Contractor Contact',
        'contractor contact',
        'Extract details of any contractor contacts mentioned in the document, including names, roles, or contact details.',
        TRUE,
        NULL
    ),
    (
        'Date',
        'date',
        'Extract all mentioned dates, including contextual information where available.',
        TRUE,
        NULL
    ),
    (
        'Address',
        'address',
        'Extract all addresses mentioned, including full addresses and any broken-down components like city or postcode.',
        TRUE,
        NULL
    ),
    (
        'BGS',
        'BGS ID',
        'Extract British Geological Survey (BGS) identifiers, references, or borehole codes.',
        TRUE,
        NULL
    )
ON CONFLICT DO NOTHING;

-- Insert BGS Classifications
INSERT INTO bgs_classifications (
    document_id, code, explanation, tooltip, applied_at
)
VALUES
    (
        '01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K',
        '426100',
        'Borehole record identifier assigned by British Geological Survey',
        'BGS ID: 426100, SU72SW51, Petersfield',
        '2024-12-17 10:32:00'
    ),
    (
        '01FCBACZSU72SW59',
        '12709323',
        'Borehole record identifier assigned by British Geological Survey',
        'BGS ID: 12709323, SU72SW59, Petersfield',
        '2024-12-17 10:32:00'
    ),
    (
        '01FCBACZSU72SE15',
        '426030',
        'Borehole record identifier assigned by British Geological Survey',
        'BGS ID: 426030, SU72SE15, Petersfield',
        '2024-12-17 10:32:00'
    ),
    (
        '01FCBACZSU72SW60',
        '15952134',
        'Borehole record identifier assigned by British Geological Survey',
        'BGS ID: 15952134, SU72SW60, Petersfield',
        '2024-12-17 10:32:00'
    )
ON CONFLICT DO NOTHING;

-- Insert User Edits
INSERT INTO user_edits (
    document_id, field, original_value, edited_value, edited_by, edited_at, reason
)
VALUES
    (
        '01FCBACZSU72SW59',
        'ISO2',
        'unknown',
        'BGS',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '2024-12-17 10:33:00',
        NULL
    ),
    (
        '01FCBACZSU72SE15',
        'ISO2',
        'unknown',
        'BGS',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '2024-12-17 10:33:00',
        NULL
    ),
    (
        '01FCBACZSU72SE15',
        'ISO4',
        'unknown',
        'SP',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '2024-12-17 10:33:00',
        NULL
    ),
    (
        '01FCBACZSU72SW60',
        'ISO2',
        'unknown',
        'BGS',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '2024-12-17 10:33:00',
        NULL
    ),
    (
        '01FCBACZSU72SW60',
        'ISO4',
        'unknown',
        'SP',
        '354a020c-cf84-4e30-afd3-07ba0b07c4fc',
        '2024-12-17 10:33:00',
        NULL
    )
ON CONFLICT DO NOTHING;

-- Commit transaction
COMMIT;


-- Query to retrieve document details by ID
SELECT 
    jsonb_build_object(
        'name', d.name,
        'source', d.source,
        'file_name', d.file_name,
        'lastModifiedDate', d.last_modified_date_time,
        'size', d.size,
        'id', d.id,
        'site_id', d.site_id,
        'drive_id', d.drive_id,
        'label', d.label,
        'type', d.type,
        '@microsoft.graph.downloadUrl', d.download_url,
        'createdBy', jsonb_build_object(
            'id', u.id,
            'email', u.email,
            'displayName', u.display_name
        ),
        'createdDateTime', d.created_date_time,
        'lastModifiedBy', jsonb_build_object(
            'id', lm.id,
            'email', lm.email,
            'displayName', lm.display_name
        ),
        'lastModifiedDateTime', d.last_modified_date_time,
        'parentReference', jsonb_build_object(
            'id', f.id,
            'name', f.name,
            'path', f.path,
            'driveType', f.drive_type,
            'driveId', f.drive_id,
            'siteId', f.site_id
        ),
        'webUrl', d.web_url,
        'cTag', v.c_tag,
        'eTag', v.e_tag,
        'file', jsonb_build_object(
            'hashes', jsonb_build_object('quickXorHash', m.quick_xor_hash),
            'mimeType', m.mime_type
        ),
        'fileSystemInfo', jsonb_build_object(
            'createdDateTime', m.created_date_time,
            'lastModifiedDateTime', m.last_modified_date_time
        ),
        'shared', jsonb_build_object('scope', m.shared_scope),
        'status', d.status
    ) AS document
FROM documents d
LEFT JOIN users u ON d.created_by = u.id
LEFT JOIN users lm ON d.last_modified_by = lm.id
LEFT JOIN folders f ON d.parent_folder_id = f.id
LEFT JOIN file_metadata m ON d.id = m.document_id
LEFT JOIN versions v ON d.id = v.document_id
WHERE d.id = '01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K';
