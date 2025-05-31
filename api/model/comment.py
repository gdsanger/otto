from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class Comment(BaseModel):
    """Eine zeitgestempelte Notiz oder E-Mail zu einer Aufgabe."""

    datum: datetime
    task_id: str
    user_id: str
    text: str
    type: Literal["note", "email_in", "email_out"] = "note"
    message_id: Optional[str] = None
