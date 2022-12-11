from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class LoginRequest:
    name: str
    password: str
    type: str = "login"


@dataclass_json
@dataclass
class MessageRequest:
    text: str
    type: str = "message"


@dataclass_json
@dataclass
class OkResponse:
    status: str = "ok"


@dataclass_json
@dataclass
class ErrResponse:
    error: str
    status: str = "error"