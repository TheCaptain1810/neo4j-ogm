from fastapi import FastAPI, Depends, HTTPException
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
import os
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

class Neo4jConnection:
    def __init__(self):
        try:
            self.driver = AsyncGraphDatabase.driver(
                os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
                auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
            )
            logger.info("Neo4j connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
            raise

    async def close(self):
        await self.driver.close()
        logger.info("Neo4j connection closed")

    async def query(self, query, parameters=None):
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                data = [dict(record) for record in await result.data()]
                logger.debug(f"Query executed: {query[:50]}... with params: {parameters}")
                return data
        except Exception as e:
            logger.error(f"Query failed: {query[:50]}... Error: {str(e)}")
            raise

async def get_db():
    db = Neo4jConnection()
    try:
        yield db
    finally:
        await db.close()

# Pydantic models
class UserCreate(BaseModel):
    id: str
    email: str
    displayName: str

class FolderCreate(BaseModel):
    id: str
    name: str
    path: str
    driveType: str
    driveId: str
    siteId: str

class DocumentCreate(BaseModel):
    id: str
    name: str
    label: str
    size: int
    file_name: Optional[str]
    source: str
    type: str
    createdDateTime: str
    lastModifiedDateTime: str
    webUrl: str
    downloadUrl: str
    driveId: str
    siteId: str
    status: str
    description: Optional[str]
    parentReference_id: str
    createdBy: str
    lastModifiedBy: str

class Document(BaseModel):
    id: str
    name: str
    label: str
    size: int
    file_name: Optional[str]
    source: str
    type: str
    createdDateTime: str
    lastModifiedDateTime: str
    webUrl: str
    downloadUrl: str
    driveId: str
    siteId: str
    status: str
    description: Optional[str]
    parentReference_id: Optional[str]
    createdBy: Optional[str]
    lastModifiedBy: Optional[str]

class FileMetadataCreate(BaseModel):
    documentId: str
    mimeType: str
    quickXorHash: str
    sharedScope: str
    createdDateTime: str
    lastModifiedDateTime: str

class VersionCreate(BaseModel):
    documentId: str
    eTag: str
    cTag: str
    timestamp: str
    versionNumber: int

class SessionCreate(BaseModel):
    sessionId: str
    sessionName: str
    createdAt: str
    createdBy: str
    fileCount: int
    completedAt: Optional[str]
    status: str
    warnings: int
    rowCount: int

class ClassifierCreate(BaseModel):
    id: str
    name: str
    isHierarchy: bool
    parentId: Optional[str]
    prompt: str
    description: str

class ClassifierDataCreate(BaseModel):
    classifierId: str
    code: str
    description: str
    prompt: Optional[str]

class EnricherCreate(BaseModel):
    name: str
    searchTerm: str
    body: str
    active: bool
    value: Optional[str]

class BGSClassificationCreate(BaseModel):
    documentId: str
    code: str
    explanation: str
    tooltip: str
    appliedAt: str

class UserEditCreate(BaseModel):
    documentId: str
    field: str
    originalValue: str
    editedValue: str
    editedBy: str
    editedAt: str
    reason: Optional[str]

class AIEditExport(BaseModel):
    documentId: str
    field: str
    originalValue: str
    editedValue: str
    editedAt: str

class SessionStandardExport(BaseModel):
    classifiers: List[ClassifierCreate]
    enrichers: List[EnricherCreate]

@app.on_event("startup")
async def startup_event():
    db = Neo4jConnection()
    try:
        await db.query("""
        CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.sessionId IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT classifier_id_unique IF NOT EXISTS FOR (c:Classifier) REQUIRE c.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT folder_id_unique IF NOT EXISTS FOR (f:Folder) REQUIRE f.id IS UNIQUE
        """)
        await db.query("""
        CREATE INDEX document_name_index IF NOT EXISTS FOR (d:Document) ON (d.name)
        """)
        await db.query("""
        CREATE INDEX document_created_index IF NOT EXISTS FOR (d:Document) ON (d.createdDateTime)
        """)
        logger.info("Constraints and indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating constraints/indexes: {str(e)}")
        raise
    finally:
        await db.close()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        CREATE (u:User {id: $id, email: $email, displayName: $displayName})
        RETURN u
        """
        result = await db.query(query, user.dict())
        logger.info(f"Created user: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Error creating user {user.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@app.post("/folders/", response_model=FolderCreate)
async def create_folder(folder: FolderCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        CREATE (f:Folder {id: $id, name: $name, path: $path, driveType: $driveType, driveId: $driveId, siteId: $siteId})
        RETURN f
        """
        result = await db.query(query, folder.dict())
        logger.info(f"Created folder: {folder.id}")
        return folder
    except Exception as e:
        logger.error(f"Error creating folder {folder.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating folder: {str(e)}")

@app.post("/documents/", response_model=DocumentCreate)
async def create_document(document: DocumentCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (u:User {id: $createdBy}), (lm:User {id: $lastModifiedBy}), (f:Folder {id: $parentReference_id})
        CREATE (d:Document {id: $id, name: $name, label: $label, size: $size, file_name: $file_name,
                           source: $source, type: $type, createdDateTime: $createdDateTime,
                           lastModifiedDateTime: $lastModifiedDateTime, webUrl: $webUrl,
                           downloadUrl: $downloadUrl, driveId: $driveId, siteId: $siteId,
                           status: $status, description: $description})
        CREATE (d)-[:CREATED_BY]->(u)
        CREATE (d)-[:LAST_MODIFIED_BY]->(lm)
        CREATE (d)-[:STORED_IN]->(f)
        RETURN d
        """
        result = await db.query(query, document.dict())
        if not result:
            logger.error(f"Document creation failed for {document.id}: No result returned")
            raise HTTPException(status_code=400, detail="Document creation failed: No result")
        logger.info(f"Created document: {document.id}")
        return document
    except Exception as e:
        logger.error(f"Error creating document {document.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating document: {str(e)}")

@app.post("/file-metadata/", response_model=FileMetadataCreate)
async def create_file_metadata(metadata: FileMetadataCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $documentId})
        CREATE (m:FileMetadata {documentId: $documentId, mimeType: $mimeType, quickXorHash: $quickXorHash,
                                sharedScope: $sharedScope, createdDateTime: $createdDateTime,
                                lastModifiedDateTime: $lastModifiedDateTime})
        CREATE (d)-[:HAS_METADATA]->(m)
        RETURN m
        """
        result = await db.query(query, metadata.dict())
        logger.info(f"Created file metadata for document: {metadata.documentId}")
        return metadata
    except Exception as e:
        logger.error(f"Error creating file metadata for {metadata.documentId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating file metadata: {str(e)}")

@app.post("/versions/", response_model=VersionCreate)
async def create_version(version: VersionCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $documentId})
        CREATE (v:Version {documentId: $documentId, eTag: $eTag, cTag: $cTag,
                          timestamp: $timestamp, versionNumber: $versionNumber})
        CREATE (d)-[:HAS_VERSION]->(v)
        RETURN v
        """
        result = await db.query(query, version.dict())
        logger.info(f"Created version for document: {version.documentId}")
        return version
    except Exception as e:
        logger.error(f"Error creating version for {version.documentId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating version: {str(e)}")

@app.post("/sessions/", response_model=SessionCreate)
async def create_session(session: SessionCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        CREATE (s:Session {sessionId: $sessionId, sessionName: $sessionName, createdAt: $createdAt,
                          createdBy: $createdBy, fileCount: $fileCount, completedAt: $completedAt,
                          status: $status, warnings: $warnings, rowCount: $rowCount})
        RETURN s
        """
        result = await db.query(query, session.dict())
        logger.info(f"Created session: {session.sessionId}")
        return session
    except Exception as e:
        logger.error(f"Error creating session {session.sessionId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating session: {str(e)}")

@app.post("/classifiers/", response_model=ClassifierCreate)
async def create_classifier(classifier: ClassifierCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        CREATE (c:Classifier {id: $id, name: $name, isHierarchy: $isHierarchy, parentId: $parentId,
                             prompt: $prompt, description: $description})
        RETURN c
        """
        result = await db.query(query, classifier.dict())
        logger.info(f"Created classifier: {classifier.id}")
        return classifier
    except Exception as e:
        logger.error(f"Error creating classifier {classifier.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating classifier: {str(e)}")

@app.post("/classifier-data/", response_model=ClassifierDataCreate)
async def create_classifier_data(data: ClassifierDataCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (c:Classifier {id: $classifierId})
        CREATE (d:ClassifierData {classifierId: $classifierId, code: $code, description: $description, prompt: $prompt})
        CREATE (c)-[:HAS_DATA]->(d)
        RETURN d
        """
        result = await db.query(query, data.dict())
        logger.info(f"Created classifier data {data.code} for classifier: {data.classifierId}")
        return data
    except Exception as e:
        logger.error(f"Error creating classifier data {data.code} for {data.classifierId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating classifier data: {str(e)}")

@app.post("/enrichers/", response_model=EnricherCreate)
async def create_enricher(enricher: EnricherCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        CREATE (e:Enricher {name: $name, searchTerm: $searchTerm, body: $body, active: $active, value: $value})
        RETURN e
        """
        result = await db.query(query, enricher.dict())
        logger.info(f"Created enricher: {enricher.name}")
        return enricher
    except Exception as e:
        logger.error(f"Error creating enricher {enricher.name}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating enricher: {str(e)}")

@app.post("/bgs/classifications/", response_model=BGSClassificationCreate)
async def create_bgs_classification(bgs: BGSClassificationCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $documentId})
        CREATE (b:BGSClassification {documentId: $documentId, code: $code, explanation: $explanation,
                                    tooltip: $tooltip, appliedAt: $appliedAt})
        CREATE (d)-[:HAS_BGS_CLASSIFICATION]->(b)
        RETURN b
        """
        result = await db.query(query, bgs.dict())
        logger.info(f"Created BGS classification for document: {bgs.documentId}")
        return bgs
    except Exception as e:
        logger.error(f"Error creating BGS classification for {bgs.documentId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating BGS classification: {str(e)}")

@app.post("/user-edits/", response_model=UserEditCreate)
async def create_user_edit(edit: UserEditCreate, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $documentId}), (u:User {id: $editedBy})
        CREATE (e:UserEdit {documentId: $documentId, field: $field, originalValue: $originalValue,
                            editedValue: $editedValue, editedBy: $editedBy, editedAt: $editedAt, reason: $reason})
        CREATE (d)-[:HAS_USER_EDIT]->(e)
        CREATE (e)-[:EDITED_BY]->(u)
        RETURN e
        """
        result = await db.query(query, edit.dict())
        logger.info(f"Created user edit for document: {edit.documentId}")
        return edit
    except Exception as e:
        logger.error(f"Error creating user edit for {edit.documentId}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating user edit: {str(e)}")

@app.get("/export/document/{document_id}", response_model=Document)
async def export_document(document_id: str, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $document_id})
        OPTIONAL MATCH (d)-[:CREATED_BY]->(u:User)
        OPTIONAL MATCH (d)-[:LAST_MODIFIED_BY]->(lm:User)
        OPTIONAL MATCH (d)-[:STORED_IN]->(f:Folder)
        RETURN d, u, lm, f
        """
        result = await db.query(query, {"document_id": document_id})
        if not result:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        record = result[0]
        document = record["d"]
        user = record["u"]
        last_modified_user = record["lm"]
        folder = record["f"]
        
        document_data = {
            "id": document["id"],
            "name": document["name"],
            "label": document["label"],
            "size": document.get("size", 0),
            "file_name": document.get("file_name"),
            "source": document.get("source"),
            "type": document.get("type"),
            "createdDateTime": document.get("createdDateTime"),
            "lastModifiedDateTime": document.get("lastModifiedDateTime"),
            "webUrl": document.get("webUrl"),
            "downloadUrl": document.get("downloadUrl"),
            "driveId": document.get("driveId"),
            "siteId": document.get("siteId"),
            "status": document.get("status"),
            "description": document.get("description"),
            "parentReference_id": folder["id"] if folder else None,
            "createdBy": user["id"] if user else None,
            "lastModifiedBy": last_modified_user["id"] if last_modified_user else None
        }
        logger.info(f"Exported document: {document_id}")
        return document_data
    except Exception as e:
        logger.error(f"Error exporting document {document_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting document: {str(e)}")

@app.get("/export/ai-edits", response_model=List[AIEditExport])
async def export_ai_edits(db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document)-[:HAS_AI_EDIT]->(e:AIEdit)
        RETURN d.id AS documentId, e.field AS field, e.originalValue AS originalValue,
               e.editedValue AS editedValue, e.editedAt AS editedAt
        """
        result = await db.query(query)
        logger.info("Exported AI edits")
        return [AIEditExport(**record) for record in result]
    except Exception as e:
        logger.error(f"Error exporting AI edits: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting AI edits: {str(e)}")

@app.get("/export/session/{session_id}", response_model=SessionCreate)
async def export_session(session_id: str, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (s:Session {sessionId: $session_id})
        RETURN s
        """
        result = await db.query(query, {"session_id": session_id})
        if not result:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        session = result[0]["s"]
        logger.info(f"Exported session: {session_id}")
        return SessionCreate(**session)
    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting session: {str(e)}")

@app.get("/export/session-standard", response_model=SessionStandardExport)
async def export_session_standard(db: Neo4jConnection = Depends(get_db)):
    try:
        classifiers_query = """
        MATCH (c:Classifier)
        OPTIONAL MATCH (c)-[:HAS_DATA]->(d:ClassifierData)
        RETURN c, collect(d) AS data
        """
        enrichers_query = """
        MATCH (e:Enricher)
        RETURN e
        """
        classifiers_result = await db.query(classifiers_query)
        enrichers_result = await db.query(enrichers_query)
        
        classifiers = []
        for record in classifiers_result:
            classifier = record["c"]
            classifier_data = [
                ClassifierDataCreate(classifierId=classifier["id"], code=d["code"], description=d["description"], prompt=d["prompt"])
                for d in record["data"]
            ]
            classifiers.append(ClassifierCreate(
                id=classifier["id"], name=classifier["name"], isHierarchy=classifier["isHierarchy"],
                parentId=classifier["parentId"], prompt=classifier["prompt"], description=classifier["description"]
            ))
        
        enrichers = [EnricherCreate(**e) for e in enrichers_result]
        
        logger.info("Exported session-standard data")
        return SessionStandardExport(classifiers=classifiers, enrichers=enrichers)
    except Exception as e:
        logger.error(f"Error exporting session-standard: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting session-standard: {str(e)}")

@app.get("/export/user-edits", response_model=List[UserEditCreate])
async def export_user_edits(db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document)-[:HAS_USER_EDIT]->(e:UserEdit)
        RETURN e
        """
        result = await db.query(query)
        logger.info("Exported user edits")
        return [UserEditCreate(**record["e"]) for record in result]
    except Exception as e:
        logger.error(f"Error exporting user edits: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting user edits: {str(e)}")

@app.get("/export/document/{document_id}/metadata", response_model=FileMetadataCreate)
async def export_document_metadata(document_id: str, db: Neo4jConnection = Depends(get_db)):
    try:
        query = """
        MATCH (d:Document {id: $document_id})-[:HAS_METADATA]->(m:FileMetadata)
        RETURN m
        """
        result = await db.query(query, {"document_id": document_id})
        if not result:
            logger.warning(f"Metadata not found for document: {document_id}")
            raise HTTPException(status_code=404, detail=f"Metadata not found for document: {document_id}")
        metadata = result[0]["m"]
        logger.info(f"Exported metadata for document: {document_id}")
        return FileMetadataCreate(**metadata)
    except Exception as e:
        logger.error(f"Error exporting metadata for document {document_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting metadata: {str(e)}")