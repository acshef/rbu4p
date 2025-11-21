import enum
import typing as t

from ._base import _Base
from .stack import Stack


class EndpointStatus(enum.IntEnum):
    UP = 1
    DOWN = 2


class Endpoint(_Base):
    id: int
    name: str
    status: int
    stacks: t.Optional[list["Stack"]] = None

    def __init__(self, o: dict, /):
        super().__init__(o)
        self.id = o["Id"]
        self.name = o["Name"]
        self.status = o["Status"]

    @property
    def is_up(self) -> bool:
        return self.status == EndpointStatus.UP
