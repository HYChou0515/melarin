import functools
from melarin.base import IType
from melarin.builtins import BuiltinType
import msgpack


types: list[type[IType]] = [BuiltinType]


def dec_hook(code, data):
    if code in IType._code_map:
        return IType._code_map[code].decode(data)
    return msgpack.ExtType(code, data)


def enc_hook(obj):
    if type(obj) in IType._type_map:
        t = IType._type_map[type(obj)]
        encoded = t.encode(obj)
        if encoded is not NotImplemented:
            return msgpack.ExtType(t.TYPECODE, encoded)
    for t in IType._fallbacks:
        encoded = t.encode(obj)
        if encoded is not NotImplemented:
            return msgpack.ExtType(t.TYPECODE, encoded)
    return obj


enc = functools.partial(msgpack.packb, default=enc_hook)
dec = functools.partial(msgpack.unpackb, ext_hook=dec_hook)
