import ctypes
import logging
from typing import Optional

from .library import Scopes
from .types import CastedTypeBase, CStruct
from .utils import FuncInfo, cast_type

LOGGER = logging.getLogger(__name__)


def structure(
        *,
        pack: Optional[int] = None,
        str_type: Optional[CastedTypeBase] = None,
        int_bits: Optional[int] = None,
        int_sign: Optional[bool] = None,
        scope: Optional[Scopes] = None
):
    """Class decorator for C structures definition.

    .. code-block:: python

        @structure
        class MyStruct:

            first: int
            second: str
            third: 'MyStruct'

    :param pack: Allows custom maximum alignment for the fields (as #pragma pack(n)).

    :param str_type: Type to represent strings.

    :param int_bits: int length to be used in function.

    :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

    :param scope: Scopes

    """
    params = locals()

    if scope is None:
        scope = Scopes(params)

    def wrapper(cls_):

        annotations = {
            attrname: attrhint for attrname, attrhint in cls_.__annotations__.items()
            if not attrname.startswith('_')}

        with scope(**params):

            cls_name = cls_.__name__

            info = FuncInfo(
                name_py=cls_name, name_c=None,
                annotations=annotations, options=scope.flatten())

            # todo maybe support big/little byte order
            struct = type(cls_name, (CStruct, cls_), {})

            ct_fields = {}
            fields = []

            for attrname, attrhint in annotations.items():

                if attrhint == cls_name:
                    casted = ctypes.POINTER(struct)
                    ct_fields[attrname] = struct

                else:
                    casted = cast_type(info, attrname, attrhint)

                    if issubclass(casted, CastedTypeBase):
                        ct_fields[attrname] = casted

                fields.append((attrname, casted))

            LOGGER.debug(f'Structure {cls_name} fields: {fields}')

            if pack:
                struct._pack_ = pack

            struct._ct_fields = ct_fields
            struct._fields_ = fields

        return struct

    return wrapper
