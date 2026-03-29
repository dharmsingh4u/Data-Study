from pydantic import BaseModel
from typing import Optional
from typing import Literal
from typing import Literal

class chat_class(BaseModel):
    message:str
    feedack :str
    comment:str
    thread_id :int

