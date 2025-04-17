import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from .base import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    source = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Retrieval(Base):
    __tablename__ = "retrievals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_log_id = Column(UUID(as_uuid=True), ForeignKey("query_logs.id"))
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"))
    score = Column(Float, nullable=False)
