from abc import ABC, abstractmethod
from collections.abc import Collection
import datetime as dt
from typing import Any
import struct

from melarin.base import IType


class BuiltinType(IType, ABC):
    # 自動註冊subclasses
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        BuiltinType._code_map[cls.SUBCODE] = cls
        for t in cls.TYPES:
            BuiltinType._type_map[t] = cls
        if cls.FALLBACK:
            BuiltinType._fallbacks.append(cls)
        IType.register(cls, cls.TYPES)

    _code_map: dict[int, type["BuiltinType"]] = {}
    _type_map: dict[type, type["BuiltinType"]] = {}
    _fallbacks: list[type["BuiltinType"]] = []

    TYPECODE: int = 0
    SUBCODE: int
    TYPES: Collection[type] = {}
    FALLBACK: bool = False

    @classmethod
    @abstractmethod
    def raw_encode(cls, obj: Any) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def raw_decode(cls, data: bytes) -> Any:
        pass

    @classmethod
    def encode(cls, obj: Any) -> bytes:
        if type(obj) in cls._type_map:
            t = cls._type_map[type(obj)]
            b = t.raw_encode(obj)
            if b is not NotImplemented:
                return struct.pack("B", t.SUBCODE) + b
        for t in cls._fallbacks:
            b = t.raw_encode(obj)
            if b is not NotImplemented:
                return struct.pack("B", t.SUBCODE) + b
        return NotImplemented

    @classmethod
    def decode(cls, data: bytes) -> Any:
        subcode = data[0]
        b = data[1:]
        if subcode in cls._code_map:
            t = cls._code_map[subcode]
            return t.raw_decode(b)
        raise ValueError(f"Unknown subcode: {subcode}")


class ComplexType(BuiltinType):
    SUBCODE = 0
    TYPES: Collection[type] = {complex}

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        if isinstance(obj, complex):
            # encode the complex number into a 16 byte buffer
            return struct.pack("dd", obj.real, obj.imag)
        return NotImplemented

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        real, imag = struct.unpack("dd", data)
        return complex(real, imag)


class DatetimeType(BuiltinType):
    SUBCODE = 1
    TYPES: Collection[type] = {dt.datetime}

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        if isinstance(obj, dt.datetime):
            return obj.isoformat().encode("utf-8")
        return NotImplemented

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        return dt.datetime.fromisoformat(data.decode("utf-8"))


class TimedeltaType(BuiltinType):
    SUBCODE = 2
    TYPES: Collection[type] = {dt.timedelta}

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        if isinstance(obj, dt.timedelta):
            return str(obj.total_seconds()).encode("utf-8")
        return NotImplemented

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        return dt.timedelta(seconds=float(data.decode("utf-8")))
