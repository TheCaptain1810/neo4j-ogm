from models.models import (
    Document, User, Folder, Session, 
    FileMetadata, Version, Classifier, 
    ClassifierData, Enricher, BGSClassification, UserEdit
)
from neomodel import db
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class DocumentService:
    """Service layer for Document operations using OGM"""
    
    @staticmethod
    def create_complete_document_structure(data: Dict[str, Any]) -> Document:
        """Create a complete document structure with all related entities"""
        try:
            # Create or get users
            created_by = User.nodes.get_or_none(uid=data["createdBy_id"])
            if not created_by:
                created_by = User(
                    uid=data["createdBy_id"],
                    email=data["createdBy_email"],
                    displayName=data["createdBy_displayName"]
                ).save()
            
            last_modified_by = User.nodes.get_or_none(uid=data["lastModifiedBy_id"])
            if not last_modified_by:
                last_modified_by = User(
                    uid=data["lastModifiedBy_id"],
                    email=data["lastModifiedBy_email"],
                    displayName=data["lastModifiedBy_displayName"]
                ).save()
            
            # Create or get folder
            folder = Folder.nodes.get_or_none(uid=data["parentReference_id"])
            if not folder:
                folder = Folder(
                    uid=data["parentReference_id"],
                    name=data["parentReference_name"],
                    path=data["parentReference_path"],
                    driveType=data["parentReference_driveType"],
                    driveId=data["parentReference_driveId"],
                    siteId=data["parentReference_siteId"]
                ).save()
            
            # Create or get session
            session = Session.nodes.get_or_none(sessionId=data["sessionId"])
            if not session:
                session = Session(
                    sessionId=data["sessionId"],
                    sessionName=data["sessionName"],
                    createdAt=data["session_createdAt"],
                    createdBy=data["session_createdBy"],
                    fileCount=data["session_fileCount"],
                    completedAt=data["session_completedAt"],
                    status=data["session_status"],
                    warnings=data["session_warnings"],
                    rowCount=data["session_rowCount"]
                ).save()
            
            # Create document
            document = Document(
                uid=data["id"],
                name=data["name"],
                label=data["label"],
                size=data["size"],
                file_name=data["file_name"],
                source=data["source"],
                type=data["type"],
                createdDateTime=data["createdDateTime"],
                lastModifiedDateTime=data["lastModifiedDateTime"],
                webUrl=data["webUrl"],
                downloadUrl=data["downloadUrl"],
                driveId=data["driveId"],
                siteId=data["siteId"],
                status=data["status"],
                description=data["description"],
                version=data["version"]
            ).save()
            
            # Create file metadata
            file_metadata = FileMetadata(
                documentId=data["file_documentId"],
                mimeType=data["file_mimeType"],
                quickXorHash=data["file_quickXorHash"],
                sharedScope=data["file_sharedScope"],
                createdDateTime=data["file_createdDateTime"],
                lastModifiedDateTime=data["file_lastModifiedDateTime"]
            ).save()
            
            # Create version
            version = Version(
                documentId=data["version_documentId"],
                eTag=data["version_eTag"],
                cTag=data["version_cTag"],
                timestamp=data["version_timestamp"],
                versionNumber=data["version_versionNumber"]
            ).save()
            
            # Create relationships
            document.created_by.connect(created_by)
            document.last_modified_by.connect(last_modified_by)
            document.stored_in.connect(folder)
            document.metadata.connect(file_metadata)
            document.version_info.connect(version)
            document.session.connect(session)
            
            logger.info(f"Created complete document structure for: {data['id']}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document structure: {str(e)}")
            raise
    
    @staticmethod
    def get_document_with_relations(document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document with all its related data"""
        try:
            document = Document.nodes.get_or_none(uid=document_id)
            if not document:
                return None
            
            # Get related entities using neomodel relationships
            created_by = None
            last_modified_by = None
            folder = None
            metadata = None
            version = None
            
            try:
                created_by = document.created_by.single()
                last_modified_by = document.last_modified_by.single()
                folder = document.stored_in.single()
                metadata = document.metadata.single()
                version = document.version_info.single()
            except Exception as e:
                logger.warning(f"Error getting relationships: {str(e)}")
            
            # Build response structure
            response = {
                "name": document.name,
                "source": document.source,
                "file_name": document.file_name,
                "lastModifiedDate": document.lastModifiedDateTime,
                "size": document.size,
                "id": document.uid,
                "site_id": document.siteId,
                "drive_id": document.driveId,
                "label": document.label,
                "type": document.type,
                "@microsoft.graph.downloadUrl": document.downloadUrl,
                "createdDateTime": document.createdDateTime,
                "lastModifiedDateTime": document.lastModifiedDateTime,
                "webUrl": document.webUrl,
                "status": document.status,
                "createdBy": {
                    "id": created_by.uid,
                    "email": created_by.email,
                    "displayName": created_by.displayName
                } if created_by else None,
                "lastModifiedBy": {
                    "id": last_modified_by.uid,
                    "email": last_modified_by.email,
                    "displayName": last_modified_by.displayName
                } if last_modified_by else None,
                "parentReference": {
                    "id": folder.uid,
                    "name": folder.name,
                    "path": folder.path,
                    "driveType": folder.driveType,
                    "driveId": folder.driveId,
                    "siteId": folder.siteId
                } if folder else None,
                "file": {
                    "hashes": {"quickXorHash": metadata.quickXorHash},
                    "mimeType": metadata.mimeType
                } if metadata else None,
                "fileSystemInfo": {
                    "createdDateTime": metadata.createdDateTime,
                    "lastModifiedDateTime": metadata.lastModifiedDateTime
                } if metadata else None,
                "shared": {
                    "scope": metadata.sharedScope
                } if metadata else None,
                "cTag": version.cTag if version else None,
                "eTag": version.eTag if version else None
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_all_documents():
        """Delete all documents and related data"""
        try:
            # Delete all nodes using Cypher
            db.cypher_query("MATCH (n) DETACH DELETE n")
            
            logger.info("All documents and related data deleted")
            
        except Exception as e:
            logger.error(f"Error deleting all data: {str(e)}")
            raise


class UserService:
    """Service layer for User operations"""
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        return User(**user_data).save()
    
    @staticmethod
    def get_user(user_id: str) -> Optional[User]:
        """Get user by ID"""
        return User.nodes.get_or_none(uid=user_id)


class SessionService:
    """Service layer for Session operations"""
    
    @staticmethod
    def create_session(session_data: Dict[str, Any]) -> Session:
        """Create a new session"""
        return Session(**session_data).save()
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return Session.nodes.get_or_none(sessionId=session_id)


class ClassifierService:
    """Service layer for Classifier operations"""
    
    @staticmethod
    def create_classifier(classifier_data: Dict[str, Any]) -> Classifier:
        """Create a new classifier"""
        return Classifier(**classifier_data).save()
    
    @staticmethod
    def get_classifier(classifier_id: str) -> Optional[Classifier]:
        """Get classifier by ID"""
        return Classifier.nodes.get_or_none(uid=classifier_id)
    
    @staticmethod
    def get_all_classifiers() -> List[Classifier]:
        """Get all classifiers"""
        return list(Classifier.nodes.all())
