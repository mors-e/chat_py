from typing import List
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime


@dataclass_json
@dataclass
class Room:
    users: List[str]
    name: str


@dataclass_json
@dataclass
class Message:
    user: str
    text: str
    time: datetime
