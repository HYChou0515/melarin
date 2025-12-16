from abc import ABC, abstractmethod
from collections.abc import Callable, Collection
import io
import struct
from typing import Any
import numpy as np

from melarin.base import IType


class NumpyType(IType, ABC):
    # 自動註冊subclasses
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        NumpyType._code_map[cls.SUBCODE] = cls
        for t in cls.TYPES:
            NumpyType._type_map[t] = cls
        if cls.FALLBACK:
            NumpyType._fallbacks.append(cls)
        IType.register(cls, cls.TYPES)
        if cls.CHECK is not None:
            NumpyType._checks.append((cls.CHECK, cls))
            IType.register_check(cls, cls.CHECK)

    _code_map: dict[int, type["NumpyType"]] = {}
    _type_map: dict[type, type["NumpyType"]] = {}
    _fallbacks: list[type["NumpyType"]] = []
    _checks: list[tuple[Callable[[Any], bool], type["NumpyType"]]] = []

    TYPECODE: int = 1
    SUBCODE: int
    TYPES: Collection[type] = {}
    FALLBACK: bool = False
    CHECK: Callable[[Any], bool] | None = None

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        bio = io.BytesIO()
        np.save(bio, obj, allow_pickle=False)
        bio.seek(0)
        return bio.read()

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
        for check, t in cls._checks:
            if check(obj):
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


class ScalarType(NumpyType):
    SUBCODE = 0
    TYPES: Collection[type] = {np.generic}

    @classmethod
    def CHECK(cls, obj: Any) -> bool:
        return isinstance(obj, np.generic)

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        bio = io.BytesIO(data)
        bio.seek(0)
        arr = np.load(bio, allow_pickle=False)
        return arr.dtype.type(arr)


class ArrayType(NumpyType):
    SUBCODE = 1
    TYPES: Collection[type] = {np.ndarray}

    @classmethod
    def CHECK(cls, obj: Any) -> bool:
        return isinstance(obj, np.ndarray)

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        bio = io.BytesIO(data)
        bio.seek(0)
        return np.load(bio, allow_pickle=False)
