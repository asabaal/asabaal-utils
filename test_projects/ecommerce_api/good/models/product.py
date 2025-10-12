from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float
    category: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()