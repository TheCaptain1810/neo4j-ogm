from neomodel import config, db
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jOGMConnection:
    """Neo4j OGM Database connection wrapper"""
    
    def __init__(self):
        self.database = None
        self.connect()
    
    def connect(self):
        """Initialize the database connection"""
        try:
            uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            # Configure neomodel
            config.DATABASE_URL = f"bolt://{username}:{password}@{uri.replace('neo4j://', '').replace('bolt://', '')}"
            
            # Test the connection
            db.cypher_query("RETURN 1")
            
            logger.info("Neo4j OGM connection initialized with neomodel")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j OGM connection: {str(e)}")
            raise
    
    def install_all_labels(self):
        """Install all model labels and constraints"""
        try:
            # Import models to ensure they are registered
            from models.models import Document, User, Folder, Session, FileMetadata, Version
            
            # Install model labels and constraints
            from neomodel import install_all_labels
            install_all_labels()
            
            logger.info("OGM models and constraints installed successfully")
        except Exception as e:
            logger.error(f"Error installing labels: {str(e)}")
            raise
    
    def get_database(self):
        """Get the database instance"""
        return db
    
    def close(self):
        """Close the database connection"""
        try:
            # neomodel handles connection pooling automatically
            logger.info("Neo4j OGM connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")


# Global database instance
db_connection = Neo4jOGMConnection()
database = db_connection.get_database()
