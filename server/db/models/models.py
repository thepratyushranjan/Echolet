from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, JSON, ForeignKey, Float, Enum
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


Base = declarative_base()

class LanchainPgCollection(Base):
    __tablename__ = "langchain_pg_collection"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    cmetadata = Column(JSON, nullable=True)

class LangchainPgEmbedding(Base):
    __tablename__ = "langchain_pg_embedding"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(UUID(as_uuid=True), 
                           ForeignKey("langchain_pg_collection.uuid"), 
                           nullable=False)
    embedding = Column(Vector(), nullable=False)
    document = Column(String, nullable=False)
    cmetadata = Column(JSONB, nullable=True)

