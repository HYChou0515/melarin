from collections.abc import Collection
import io
from typing import Any
import numpy as np

from melarin.base import IType


class NumpyType(IType):
    TYPECODE: int = 1
    TYPES: Collection[type] = {
        np.ndarray,
    }
    FALLBACK: bool = True

    @classmethod
    def encode(cls, obj: Any) -> bytes:
        bio = io.BytesIO()
        np.save(bio, obj, allow_pickle=False)
        bio.seek(0)
        return bio.read()

    @classmethod
    def decode(cls, data: bytes) -> Any:
        bio = io.BytesIO(data)
        bio.seek(0)
        return np.load(bio, allow_pickle=False)
