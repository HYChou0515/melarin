from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any, Callable
from logging import getLogger

logger = getLogger(__name__)


class IType(ABC):
    TYPECODE: int
    TYPES: Collection[type]
    CHECK: Callable[[Any], bool] | None = None
    FALLBACK: bool

    # 自動註冊subclasses
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.__name__ == "ISubType":
            return
        if cls.TYPECODE in cls._code_map:
            logger.warning(f"TYPECODE {cls.TYPECODE} already registered")
            logger.warning(f"Overriding {cls._code_map[cls.TYPECODE]} with {cls}")
        IType._code_map[cls.TYPECODE] = cls
        for t in cls.TYPES:
            IType._type_map[t] = cls
        if cls.FALLBACK:
            IType._fallbacks.append(cls)
        if cls.CHECK is not None:
            IType._checks.append((cls.CHECK, cls))

    @classmethod
    def register(cls, t: type["IType"], types: Collection[type]) -> None:
        for tp in types:
            cls._type_map[tp] = t

    @classmethod
    def register_check(cls, t: type["IType"], check: Callable[[Any], bool]) -> None:
        cls._checks.append((check, t))

    _code_map: dict[int, type["IType"]] = {}
    _type_map: dict[type, type["IType"]] = {}
    _checks: list[tuple[Callable[[Any], bool], type["IType"]]] = []
    _fallbacks: list[type["IType"]] = []

    @classmethod
    @abstractmethod
    def encode(cls, obj: Any) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def decode(cls, data: bytes) -> Any:
        pass


class ISubType(IType, ABC):
    SUBCODE: int
    TYPES: Collection[type] = {}
    CHECK: Callable[[Any], bool] | None = None


def subclass_init_register(cls: type[IType], subcls: type[ISubType]) -> None:
    cls._code_map[subcls.SUBCODE] = subcls
    for t in subcls.TYPES:
        cls._type_map[t] = subcls
    if subcls.FALLBACK:
        cls._fallbacks.append(subcls)
    IType.register(subcls, subcls.TYPES)
    if subcls.CHECK is not None:
        cls._checks.append((subcls.CHECK, subcls))
        IType.register_check(subcls, subcls.CHECK)
