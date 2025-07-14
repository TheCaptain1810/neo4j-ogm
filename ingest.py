import requests
import json
import logging
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI server URL
BASE_URL = "http://localhost:5000"

# Neo4j connection settings
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"

# JSON data from provided files
CLASSIFIER_DATA = [
    {
        "id": "ISO1",
        "name": "Project",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify any keywords or codes related to project names, phases, specific locations, or team allocations.",
        "description": "Identifies the project or area linked to this document.",
        "data": [
            {"code": "XXXV", "description": "Non-specific to project", "prompt": ""},
            {"code": "HOPPA", "description": "Hoppa Technologies Limited", "prompt": ""},
            {"code": "EHCRA", "description": "East Hampshire Petersfield Climate Resilience Audit & Geological Assessments", "prompt": None}
        ]
    },
    {
        "id": "ISO2",
        "name": "Originator",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify any organization names, initials, or references indicating authorship or originating party.",
        "description": "Determines the organization originating this document.",
        "data": [
            {"code": "HOP", "description": "Hoppa Technologies", "prompt": "Locate mentions of 'Hoppa Technologies' or shortened references."},
            {"code": "SER", "description": "Generic Services Provider; unspecified", "prompt": "Identify mentions of generic terms like 'service provider', 'contractor', or 'subcontractor'."},
            {"code": "CLN", "description": "Generic Client Organisation; unspecified", "prompt": "Search for generic client-related terms like 'client', 'customer', 'organization'."},
            {"code": "BGS", "description": "British Geological Survey", "prompt": None}
        ]
    },
    {
        "id": "ISO3",
        "name": "Functional Breakdown",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify terms pointing to business functions or domains, such as finance, risk, commercial, legal, or operations.",
        "description": "Defines the document’s functional area, e.g., finance or legal.",
        "data": [
            {"code": "ZZ", "description": "Applies to all functional areas", "prompt": "Confirm if applicable across all functions or departments."},
            {"code": "XX", "description": "Non-specific to functional area", "prompt": "Check for non-functional or general terms, indicating broad relevance."},
            {"code": "FN", "description": "Financial, commercial, risk", "prompt": "Identify any references to financial terms, economic analysis, risk management, or corporate finance."},
            {"code": "LG", "description": "Legal, insurance, liability", "prompt": "Locate mentions of legal compliance, contracts, liability, or regulatory terms."},
            {"code": "VG", "description": "Surveys; geotechnical, environmental, other", "prompt": None},
            {"code": "HS", "description": "Health and Safety", "prompt": None},
            {"code": "TP", "description": "Town, infrastructure planning", "prompt": None},
            {"code": "ED", "description": "Engineering", "prompt": None},
            {"code": "AC", "description": "Approvals & consents", "prompt": None}
        ]
    },
    {
        "id": "ISO4",
        "name": "Spatial Breakdown",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify references to physical layouts, levels, specific locations, site planning, or building zones.",
        "description": "Specifies the physical area, such as a site or floor plan.",
        "data": [
            {"code": "ZZ", "description": "Relevant to all physical areas", "prompt": "Confirm if relevant across all physical sites, levels, or sections."},
            {"code": "XX", "description": "Non-specific to physical areas", "prompt": "Identify terms showing no specific physical location or layout."},
            {"code": "SP", "description": "Site Plan; layouts", "prompt": "Look for terms related to site-wide layouts, zoning, or external areas."},
            {"code": "FP", "description": "Floor Plan; layouts", "prompt": "Identify mentions of floor plans, interior layouts, or vertical arrangement across floors."}
        ]
    },
    {
        "id": "ISO5",
        "name": "Type",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify document format types like technical, financial, or contractual documents.",
        "description": "Identifies the document type or format.",
        "data": [
            {"code": "ZZ", "description": "Applies to all document types", "prompt": "Confirm if applicable across all document formats."},
            {"code": "XX", "description": "Non-specific to document type", "prompt": "Identify terms showing no specific document format."},
            {"code": "CN", "description": "Contractual", "prompt": "Locate terms related to contracts, agreements, or legal obligations."},
            {"code": "FN", "description": "Financial", "prompt": "Identify references to financial data, budgets, or costings."},
            {"code": "TC", "description": "Technical; reports, surveys", "prompt": "Look for technical terms related to reports, surveys, or engineering."},
            {"code": "LG", "description": "Legal", "prompt": None}
        ]
    },
    {
        "id": "ISO6",
        "name": "Discipline",
        "isHierarchy": False,
        "parentId": None,
        "prompt": "Identify terms related to professional disciplines, such as engineering, architecture, or geology.",
        "description": "Identifies the professional discipline associated with the document.",
        "data": [
            {"code": "ZZ", "description": "All disciplines", "prompt": "Confirm if relevant across all professional disciplines."},
            {"code": "XX", "description": "Non-specific to discipline", "prompt": "Identify terms showing no specific professional discipline."},
            {"code": "GE", "description": "Geology, geotechnical", "prompt": "Locate terms related to geological surveys, geotechnical engineering, or soil analysis."},
            {"code": "CV", "description": "Civil", "prompt": None},
            {"code": "AR", "description": "Architecture", "prompt": None}
        ]
    }
]

ENRICHER_DATA = [
    {
        "name": "Client",
        "searchTerm": "client",
        "body": "Extract name(s) of client(s) mentioned in the document.",
        "active": True,
        "value": None
    },
    {
        "name": "Client Contact",
        "searchTerm": "client contact",
        "body": "Extract details of any client contacts mentioned in the document, including names, roles, or contact details.",
        "active": True,
        "value": None
    },
    {
        "name": "Contractor",
        "searchTerm": "contractor",
        "body": "Extract name(s) of contractor(s) mentioned in the document.",
        "active": True,
        "value": None
    },
    {
        "name": "Contractor Contact",
        "searchTerm": "contractor contact",
        "body": "Extract details of any contractor contacts mentioned in the document, including names, roles, or contact details.",
        "active": True,
        "value": None
    },
    {
        "name": "Date",
        "searchTerm": "date",
        "body": "Extract all mentioned dates, including contextual information where available.",
        "active": True,
        "value": None
    },
    {
        "name": "Address",
        "searchTerm": "address",
        "body": "Extract all addresses mentioned, including full addresses and any broken-down components like city or postcode.",
        "active": True,
        "value": None
    },
    {
        "name": "BGS",
        "searchTerm": "BGS ID",
        "body": "Extract British Geological Survey (BGS) identifiers, references, or borehole codes.",
        "active": True,
        "value": None
    }
]

USER_DATA = {
    "id": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
    "email": "tom@hoppa.ai",
    "displayName": "Tom Goldsmith"
}

FOLDER_DATA = {
    "id": "01FCBACZKAABKJMBSJT5CJHMDH26OD3W33",
    "name": "Borehole Records - Petersfield",
    "path": "/drives/b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu/root:/Main/Sample Documents/Borehole Records - Petersfield",
    "driveType": "documentLibrary",
    "driveId": "b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu",
    "siteId": "54aef708-d676-4c8d-83ff-d76803a4ddea"
}

DOCUMENT_DATA = {
    "id": "01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
    "name": "BGS borehole 426100 (SU72SW51).pdf",
    "label": "BGS borehole 426100 (SU72SW51).pdf",
    "size": 3040,
    "file_name": None,
    "source": "sharepoint",
    "type": "application/pdf",
    "createdDateTime": "2024-12-17T10:31:25Z",
    "lastModifiedDateTime": "2024-12-17T10:31:25Z",
    "webUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%20426100%20(SU72SW51).pdf",
    "downloadUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=ad57b405-4826-4162-8ca7-b406103c6fca&Translate=false&tempauth=v1.eyJzaXRlaWQiOiI1NGFlZjcwOC1kNjc2LTRjOGQtODNmZi1kNzY4MDNhNGRkZWEiLCJhcHBfZGlzcGxheW5hbWUiOiJIb3BwYSIsImFwcGlkIjoiZmEyY2Y0YzUtZjM5ZC00Zjc1LWEzMjAtMDI5MWFkMmYxMGM1IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL2hvcHBhdGVjaG5vbG9naWVzLnNoYXJlcG9pbnQuY29tQGJhYWNjMGViLTA5MGYtNGZjOC05ZjczLWQ4YWY0ZGE5NzUwZCIsImV4cCI6IjE3NTA5NTA2NDkifQ.CkAKDGVudHJhX2NsYWltcxIwQ01paTljSUdFQUFhRm5CV05XWkRiVTVwVFZWSFpUTnlOMVEyVjNSbFFVRXFBQT09CjIKCmFjdG9yYXBwaWQSJDAwMDAwMDAzLTAwMDAtMDAwMC1jMDAwLTAwMDAwMDAwMDAwMAoKCgRzbmlkEgI2NBILCOy93JWpsZo-EAUaDTQwLjEyNi40MS4xNjIqLFhFaU9pZHNZU29tRUpBREtnRkhiRldockdBZ0J0c1lNQ3RDTkt6dGhVZVk9MJkBOAFCEKGr7AiWQADQLJpfTCAo47xKEGhhc2hlZHByb29mdG9rZW5SCFsia21zaSJdaiQwMDJlYjkwOS1mOTFmLWY0NGEtNWJjYy1jMDBkYmQ5NjU3YjFyKTBoLmZ8bWVtYmVyc2hpcHwxMDAzMjAwMzcyNzUwM2FkQGxpdmUuY29tegEyggESCevArLoPCchPEZ9z2K9NqXUNkgEDVG9tmgEJR29sZHNtaXRoogEMdG9tQGhvcHBhLmFpqgEQMTAwMzIwMDM3Mjc1MDNBRLIBgQFteWZpbGVzLnJlYWQgYWxsZmlsZXMucmVhZCBhbGxmaWxlcy53cml0ZSBhbGxzaXRlcy5yZWFkIHNlbGVjdGVkc2l0ZXMgQmFzaWNQcm9qZWN0QWxsLlJlYWQgQmFzaWNQcm9qZWN0QWxsLldyaXRlIGFsbHByb2ZpbGVzLnJlYWTIAQE.WJruvtm0fe0vZOngDiK5agUrDobTWQSRC0b7cm0qLH8&ApiVersion=2.0",
    "driveId": "b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu",
    "siteId": "54aef708-d676-4c8d-83ff-d76803a4ddea",
    "status": "N/A",
    "description": None,
    "parentReference_id": "01FCBACZKAABKJMBSJT5CJHMDH26OD3W33",
    "createdBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
    "lastModifiedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc"
}

FILE_METADATA_DATA = {
    "documentId": "01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
    "mimeType": "application/pdf",
    "quickXorHash": "yXrJBwDlOIJTPw9eEQO6o2UT8NE=",
    "sharedScope": "users",
    "createdDateTime": "2024-12-17T10:31:25Z",
    "lastModifiedDateTime": "2024-12-17T10:31:25Z"
}

VERSION_DATA = {
    "documentId": "01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
    "eTag": "\"{AD57B405-4826-4162-8CA7-B406103C6FCA},1\"",
    "cTag": "\"c:{AD57B405-4826-4162-8CA7-B406103C6FCA},1\"",
    "timestamp": "2024-12-17T10:31:25Z",
    "versionNumber": 1
}

SESSION_DATA = {
    "sessionId": "soft-mails-cry",
    "sessionName": "Engineering Design - Ground Investigation Records",
    "createdAt": "2024-11-09T15:28:55.609Z",
    "createdBy": "Tom Goldsmith",
    "fileCount": 52,
    "completedAt": None,
    "status": "draft",
    "warnings": 0,
    "rowCount": 0
}

ADDITIONAL_DOCUMENTS = [
    {
        "id": "01FCBACZSU72SW59",
        "name": "BGS borehole 12709323 (SU72SW59).pdf",
        "label": "BGS borehole 12709323 (SU72SW59).pdf",
        "size": 3040,
        "file_name": None,
        "source": "sharepoint",
        "type": "application/pdf",
        "createdDateTime": "2024-12-17T10:31:25Z",
        "lastModifiedDateTime": "2024-12-17T10:31:25Z",
        "webUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%2012709323%20(SU72SW59).pdf",
        "downloadUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example1",
        "driveId": "b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu",
        "siteId": "54aef708-d676-4c8d-83ff-d76803a4ddea",
        "status": "N/A",
        "description": None,
        "parentReference_id": "01FCBACZKAABKJMBSJT5CJHMDH26OD3W33",
        "createdBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "lastModifiedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc"
    },
    {
        "id": "01FCBACZSU72SE15",
        "name": "BGS borehole 426030 (SU72SE15).pdf",
        "label": "BGS borehole 426030 (SU72SE15).pdf",
        "size": 3040,
        "file_name": None,
        "source": "sharepoint",
        "type": "application/pdf",
        "createdDateTime": "2024-12-17T10:31:25Z",
        "lastModifiedDateTime": "2024-12-17T10:31:25Z",
        "webUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%20426030%20(SU72SE15).pdf",
        "downloadUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example2",
        "driveId": "b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu",
        "siteId": "54aef708-d676-4c8d-83ff-d76803a4ddea",
        "status": "N/A",
        "description": None,
        "parentReference_id": "01FCBACZKAABKJMBSJT5CJHMDH26OD3W33",
        "createdBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "lastModifiedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc"
    },
    {
        "id": "01FCBACZSU72SW60",
        "name": "BGS borehole 15952134 (SU72SW60).pdf",
        "label": "BGS borehole 15952134 (SU72SW60).pdf",
        "size": 3040,
        "file_name": None,
        "source": "sharepoint",
        "type": "application/pdf",
        "createdDateTime": "2024-12-17T10:31:25Z",
        "lastModifiedDateTime": "2024-12-17T10:31:25Z",
        "webUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/Shared%20Documents/Main/Sample%20Documents/Borehole%20Records%20-%20Petersfield/BGS%20borehole%2015952134%20(SU72SW60).pdf",
        "downloadUrl": "https://hoppatechnologies.sharepoint.com/sites/SharePointDemoSite/_layouts/15/download.aspx?UniqueId=example3",
        "driveId": "b!CPeuVHbWjUyD_9doA6Td6m8HS9IQoW9DtDb__nkwj-M92i-qf_-pRKp11I7IA7Pu",
        "siteId": "54aef708-d676-4c8d-83ff-d76803a4ddea",
        "status": "N/A",
        "description": None,
        "parentReference_id": "01FCBACZKAABKJMBSJT5CJHMDH26OD3W33",
        "createdBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "lastModifiedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc"
    }
]

BGS_CLASSIFICATION_DATA = [
    {
        "documentId": "01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
        "code": "426100",
        "explanation": "Borehole record identifier assigned by British Geological Survey",
        "tooltip": "BGS ID: 426100, SU72SW51, Petersfield",
        "appliedAt": "2024-12-17T10:32:00Z"
    },
    {
        "documentId": "01FCBACZSU72SW59",
        "code": "12709323",
        "explanation": "Borehole record identifier assigned by British Geological Survey",
        "tooltip": "BGS ID: 12709323, SU72SW59, Petersfield",
        "appliedAt": "2024-12-17T10:32:00Z"
    },
    {
        "documentId": "01FCBACZSU72SE15",
        "code": "426030",
        "explanation": "Borehole record identifier assigned by British Geological Survey",
        "tooltip": "BGS ID: 426030, SU72SE15, Petersfield",
        "appliedAt": "2024-12-17T10:32:00Z"
    },
    {
        "documentId": "01FCBACZSU72SW60",
        "code": "15952134",
        "explanation": "Borehole record identifier assigned by British Geological Survey",
        "tooltip": "BGS ID: 15952134, SU72SW60, Petersfield",
        "appliedAt": "2024-12-17T10:32:00Z"
    }
]

USER_EDIT_DATA = [
    {
        "documentId": "01FCBACZSU72SW59",
        "field": "ISO2",
        "originalValue": "unknown",
        "editedValue": "BGS",
        "editedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "editedAt": "2024-12-17T10:33:00Z",
        "reason": None
    },
    {
        "documentId": "01FCBACZSU72SE15",
        "field": "ISO2",
        "originalValue": "unknown",
        "editedValue": "BGS",
        "editedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "editedAt": "2024-12-17T10:33:00Z",
        "reason": None
    },
    {
        "documentId": "01FCBACZSU72SE15",
        "field": "ISO4",
        "originalValue": "unknown",
        "editedValue": "SP",
        "editedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "editedAt": "2024-12-17T10:33:00Z",
        "reason": None
    },
    {
        "documentId": "01FCBACZSU72SW60",
        "field": "ISO2",
        "originalValue": "unknown",
        "editedValue": "BGS",
        "editedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "editedAt": "2024-12-17T10:33:00Z",
        "reason": None
    },
    {
        "documentId": "01FCBACZSU72SW60",
        "field": "ISO4",
        "originalValue": "unknown",
        "editedValue": "SP",
        "editedBy": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "editedAt": "2024-12-17T10:33:00Z",
        "reason": None
    }
]

def make_request(endpoint, data, method="POST"):
    """Helper function to make HTTP requests to FastAPI endpoints."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully called {endpoint} with data: {data.get('id', data.get('name', data))}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error calling {endpoint}: {str(e)} - Response: {e.response.text if e.response else 'No response'}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling {endpoint}: {str(e)}")
        raise

def verify_nodes():
    """Verify the existence of critical nodes in Neo4j."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        with driver.session() as session:
            # Verify User
            result = session.run("MATCH (u:User {id: $id}) RETURN u", id=USER_DATA["id"])
            user_count = len([record for record in result])
            logger.info(f"Found {user_count} User nodes with id {USER_DATA['id']}")
            
            # Verify Folder
            result = session.run("MATCH (f:Folder {id: $id}) RETURN f", id=FOLDER_DATA["id"])
            folder_count = len([record for record in result])
            logger.info(f"Found {folder_count} Folder nodes with id {FOLDER_DATA['id']}")
            
            # Verify Documents
            doc_ids = [DOCUMENT_DATA["id"]] + [doc["id"] for doc in ADDITIONAL_DOCUMENTS]
            result = session.run("MATCH (d:Document) WHERE d.id IN $ids RETURN d.id", ids=doc_ids)
            doc_count = len([record for record in result])
            logger.info(f"Found {doc_count} Document nodes out of {len(doc_ids)} expected")
            
            # Verify Session
            result = session.run("MATCH (s:Session {sessionId: $sessionId}) RETURN s", sessionId=SESSION_DATA["sessionId"])
            session_count = len([record for record in result])
            logger.info(f"Found {session_count} Session nodes with sessionId {SESSION_DATA['sessionId']}")
            
            # Verify User Edits
            result = session.run("MATCH (e:UserEdit) RETURN e")
            edit_count = len([record for record in result])
            logger.info(f"Found {edit_count} UserEdit nodes out of {len(USER_EDIT_DATA)} expected")
            
            # Verify relationships
            result = session.run("MATCH (d:Document)-[:HAS_USER_EDIT]->(e:UserEdit) RETURN d.id, e.documentId")
            rel_count = len([record for record in result])
            logger.info(f"Found {rel_count} HAS_USER_EDIT relationships")
            
        driver.close()
    except Exception as e:
        logger.error(f"Error verifying nodes: {str(e)}")
        raise

def ingest_user():
    """Ingest user data."""
    logger.info("Ingesting user data")
    try:
        response = make_request("users/", USER_DATA)
        logger.info(f"User ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("User already exists, skipping")
        else:
            raise

def ingest_folder():
    """Ingest folder data."""
    logger.info("Ingesting folder data")
    try:
        response = make_request("folders/", FOLDER_DATA)
        logger.info(f"Folder ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("Folder already exists, skipping")
        else:
            raise

def ingest_documents():
    """Ingest document data."""
    logger.info("Ingesting document data")
    try:
        response = make_request("documents/", DOCUMENT_DATA)
        logger.info(f"Document ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("Document already exists, skipping")
        else:
            raise
    for doc in ADDITIONAL_DOCUMENTS:
        try:
            response = make_request("documents/", doc)
            logger.info(f"Additional document {doc['id']} ingestion response: {response}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                logger.warning(f"Document {doc['id']} already exists, skipping")
            else:
                raise

def ingest_file_metadata():
    """Ingest file metadata."""
    logger.info("Ingesting file metadata")
    try:
        response = make_request("file-metadata/", FILE_METADATA_DATA)
        logger.info(f"File metadata ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("File metadata already exists, skipping")
        else:
            raise

def ingest_version():
    """Ingest version data."""
    logger.info("Ingesting version data")
    try:
        response = make_request("versions/", VERSION_DATA)
        logger.info(f"Version ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("Version already exists, skipping")
        else:
            raise

def ingest_session():
    """Ingest session data."""
    logger.info("Ingesting session data")
    try:
        response = make_request("sessions/", SESSION_DATA)
        logger.info(f"Session ingestion response: {response}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Constraint violation" in e.response.text:
            logger.warning("Session already exists, skipping")
        else:
            raise

def ingest_classifiers():
    """Ingest classifiers and their data."""
    logger.info("Ingesting classifiers and classifier data")
    for classifier in CLASSIFIER_DATA:
        classifier_data = {
            "id": classifier["id"],
            "name": classifier["name"],
            "isHierarchy": classifier["isHierarchy"],
            "parentId": classifier["parentId"],
            "prompt": classifier["prompt"],
            "description": classifier["description"]
        }
        try:
            response = make_request("classifiers/", classifier_data)
            logger.info(f"Classifier {classifier['id']} ingestion response: {response}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                logger.warning(f"Classifier {classifier['id']} already exists, skipping")
            else:
                raise
        for data_item in classifier["data"]:
            try:
                response = make_request("classifier-data/", {
                    "classifierId": classifier["id"],
                    "code": data_item["code"],
                    "description": data_item["description"],
                    "prompt": data_item["prompt"]
                })
                logger.info(f"Classifier data {data_item['code']} for {classifier['id']} ingestion response: {response}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                    logger.warning(f"Classifier data {data_item['code']} for classifier {classifier['id']} already exists, skipping")
                else:
                    raise

def ingest_enrichers():
    """Ingest enricher data."""
    logger.info("Ingesting enricher data")
    for enricher in ENRICHER_DATA:
        try:
            response = make_request("enrichers/", enricher)
            logger.info(f"Enricher {enricher['name']} ingestion response: {response}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                logger.warning(f"Enricher {enricher['name']} already exists, skipping")
            else:
                raise

def ingest_bgs_classifications():
    """Ingest BGS classifications."""
    logger.info("Ingesting BGS classifications")
    for bgs in BGS_CLASSIFICATION_DATA:
        try:
            response = make_request("bgs/classifications/", bgs)
            logger.info(f"BGS classification for document {bgs['documentId']} ingestion response: {response}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                logger.warning(f"BGS classification for document {bgs['documentId']} already exists, skipping")
            else:
                raise

def ingest_user_edits():
    """Ingest user edits."""
    logger.info("Ingesting user edits")
    for edit in USER_EDIT_DATA:
        try:
            response = make_request("user-edits/", edit)
            logger.info(f"User edit for document {edit['documentId']} ingestion response: {response}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Constraint violation" in e.response.text:
                logger.warning(f"User edit for document {edit['documentId']} already exists, skipping")
            else:
                logger.error(f"Failed to ingest user edit for document {edit['documentId']}: {str(e)}")
                raise

def verify_ingestion():
    """Verify ingested data by calling export endpoints."""
    logger.info("Verifying ingested data")
    endpoints = [
        "export/ai-edits",
        "export/document/01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
        "export/document/01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K/metadata",
        "export/session/soft-mails-cry",
        "export/user-edits",
        "export/session-standard"
    ]
    for endpoint in endpoints:
        try:
            response = make_request(endpoint, {}, method="GET")
            logger.info(f"Data from {endpoint}: {json.dumps(response, indent=2)}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error verifying {endpoint}: {str(e)} - Response: {e.response.text if e.response else 'No response'}")
            raise

def main():
    """Main function to ingest all data in the correct order."""
    try:
        ingest_user()
        ingest_folder()
        ingest_documents()
        ingest_file_metadata()
        ingest_version()
        ingest_session()
        ingest_classifiers()
        ingest_enrichers()
        ingest_bgs_classifications()
        ingest_user_edits()
        verify_nodes()
        verify_ingestion()
        logger.info("Data ingestion and verification completed successfully")
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
