# Pydantic schemas for document endpoints
from pydantic import BaseModel 

class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: str # Note: This might need adjustment based on actual data source 