from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal, Optional


@dataclass
class JobOffer:
    url: str
    source: Literal["france_travail", "wttj", "apec"]
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    contract_type: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[datetime] = None
    raw_data: Optional[dict] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        data = asdict(self)
        if isinstance(self.posted_at, datetime):
            data["posted_at"] = self.posted_at.isoformat()
        return data
