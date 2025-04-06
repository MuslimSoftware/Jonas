from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ServiceResult:
    """Result for service operations."""
    success: bool
    message: str
    data: Optional[Dict] = None