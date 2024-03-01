from fastapi import Request
from pydantic import BaseModel
from core.config import HOST, PORT

class BaseResponse(BaseModel):
    request: Request
    ip: str = HOST
    port: str = PORT
    
    class Config:
        arbitrary_types_allowed = True
        

class OutputResponse(BaseResponse):
    page_list: list