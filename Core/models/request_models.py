

from pydantic import BaseModel
class RemoveUser(BaseModel):
    email: str = None