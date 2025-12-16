from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any


class IType(ABC):
    TYPECODE: int
    TYPES: Collection[type]
    FALLBACK: bool

    # 自動註冊subclasses
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        IType._code_map[cls.TYPECODE] = cls
        for t in cls.TYPES:
            IType._type_map[t] = cls
        if cls.FALLBACK:
            IType._fallbacks.append(cls)

    @classmethod
    def register(cls, t: type["IType"], types: Collection[type]) -> None:
        for tp in types:
            cls._type_map[tp] = t

    _code_map: dict[int, type["IType"]] = {}
    _type_map: dict[type, type["IType"]] = {}
    _fallbacks: list[type["IType"]] = []

    @classmethod
    @abstractmethod
    def encode(cls, obj: Any) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def decode(cls, data: bytes) -> Any:
        pass
