from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    message: str
    error_code: Optional[str] = None
    status_code: int = 500