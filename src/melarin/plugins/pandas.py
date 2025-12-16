from abc import ABC, abstractmethod
from collections.abc import Callable
import io
import json
import struct
from typing import Any

import pandas as pd

from melarin.base import ISubType, subclass_init_register


class PandasType(ISubType, ABC):
    # 自動註冊subclasses
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        subclass_init_register(PandasType, cls)

    _code_map: dict[int, type["PandasType"]] = {}
    _type_map: dict[type, type["PandasType"]] = {}
    _fallbacks: list[type["PandasType"]] = []
    _checks: list[tuple[Callable[[Any], bool], type["PandasType"]]] = []

    TYPECODE: int = 2
    FALLBACK: bool = True

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


class ParquetFrameType(PandasType):
    SUBCODE = 0
    TYPES = {pd.DataFrame}

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        try:
            bio = io.BytesIO()
            obj.to_parquet(bio)
            return bio.getvalue()
        except ImportError:
            return NotImplemented

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        return pd.read_parquet(io.BytesIO(data))


class ParquetSeriesType(PandasType):
    SUBCODE = 1
    TYPES = {pd.Series}

    @classmethod
    def raw_encode(cls, obj: Any) -> bytes:
        df = obj.to_frame()
        try:
            bio = io.BytesIO()
            df.to_parquet(bio)
            name = json.dumps(obj.name).encode("utf-8")
            return struct.pack("BI", 0, len(name)) + name + bio.getvalue()
        except Exception:
            bio = io.BytesIO()
            df.to_json(bio)
            name = json.dumps(obj.name).encode("utf-8")
            return struct.pack("BI", 1, len(name)) + name + bio.getvalue()

    @classmethod
    def raw_decode(cls, data: bytes) -> Any:
        isdf, name_len = struct.unpack("BI", data[:8])
        isdf = isdf == 0
        name = data[8 : 8 + name_len].decode("utf-8")
        name = json.loads(name)
        b = data[8 + name_len :]
        if isdf:
            df = pd.read_parquet(io.BytesIO(b))
            s = df[df.columns[0]]
            s.name = name
            return s
        else:
            df = pd.read_json(io.BytesIO(b))
            s = df[df.columns[0]]
            s.name = name
            return s
