from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class UserSession:
    token: Optional[str] = None
    user: Dict[str, str] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None and bool(self.user)

    @property
    def role(self) -> Optional[str]:
        return self.user.get("role") if self.user else None

    def clear(self) -> None:
        self.token = None
        self.user = {}
