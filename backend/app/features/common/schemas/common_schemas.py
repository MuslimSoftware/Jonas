from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

# --- Pagination Schemas ---

T = TypeVar('T')

class PaginatedResponseData(BaseModel, Generic[T]):
    """Generic structure for paginated data responses."""
    model_config = {'from_attributes': True} # Add config for validation

    items: List[T]
    next_cursor_timestamp: Optional[datetime] = None # Timestamp of the oldest item in the current batch
    has_more: bool = False # Indicates if there are more items to fetch

class BaseResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    message: str
    error_code: Optional[str] = None
    status_code: int = 500