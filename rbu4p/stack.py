import typing as t

from ._base import _Base


class Stack(_Base):
    id: int
    endpoint_id: int
    name: str
    env: dict[str, str]
    file: str

    def __init__(self, o: dict, /, *, file: t.Optional[str] = None):
        super().__init__(o)
        self.id = o["Id"]
        self.endpoint_id = o["EndpointId"]
        self.name = o["Name"]
        self.env = dict((x["name"], x["value"]) for x in o["Env"])
        self.file = file
