from dataclasses import asdict, dataclass, field
import json
from random import random
from time import time
from typing import Any, Optional


@dataclass
class Message:
    id: str = field(init=False)
    scope: str
    data: Optional[Any] = None

    def __post_init__(self):
        self.id = f"{int(time()*1e6)}-{self.scope}-{int(random()*1e6)}"

    def json(self):
        return json.dumps(asdict(self)) + "\n"

    def encode(self):
        return self.json().encode()

    @classmethod
    def parse(cls, text):
        data = json.loads(text)
        id = data["id"]
        del data["id"]
        message = cls(**data)
        message.id = id
        return message


@dataclass
class Request(Message):
    action: Optional[str] = None


@dataclass
class Response(Message):
    correlation: Optional[str] = None
    content: Optional[str] = None

    @classmethod
    def ok(cls, request):
        return cls(
            scope=request.scope,
            content="info",
            correlation=request.id,
            data={"result": "ok"},
        )
