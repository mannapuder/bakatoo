from dataclasses import dataclass

import uuid


@dataclass
class Task:
    uuid: str = str(uuid.uuid4())
    kill: bool = False
    status: dict = None
