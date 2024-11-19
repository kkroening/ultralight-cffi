import cffi
import cffi.model
import pathlib
from textwrap import dedent
from typing import Any
from typing import TypeAlias
import logging

_HERE = pathlib.Path(__file__).parent
_ROOT_DIR = _HERE.parent
_SRC_DIR = _ROOT_DIR / 'ultralight_cffi'

_SKIP_DECL_NAMES = {
    'typedef max_align_t',
    'typedef __caddr_t',
    'typedef __fsid_t',
    'typedef __timer_t',
}

_TypeID: TypeAlias = int

_TypedefMap: TypeAlias = dict[_TypeID, tuple[cffi.model.BaseTypeByIdentity, set[str]]]

_logger = logging.getLogger(__name__)


def _get_typedef_map(
    declarations: dict[str, tuple[cffi.model.BaseTypeByIdentity, Any]],
) -> _TypedefMap:
    """Constructs a mapping of type IDs to corresponding typedef alias(es).

    CFFI type objects don't inherently keep track of whichever typedef created them.
    For example, ``ulCreateStringUTF8`` is defined in C as returning ``ULString``,
    where ``ULString`` is a typedef::

        typedef struct C_String* ULString;

        // ...

        ULString ulCreateStringUTF8(const char* str, size_t len);

    When CFFI parses this into a :class:`cffi.model.FunctionPtrType`, the ``result``
    type is ``C_String*`` rather than ``ULString``, which is legitimate in the sense
    that ``ULString`` is basically an alias (i.e. typedef) for ``C_String*``, but in
    terms of Python code generation, it's preferable to define things in terms of the
    friendlier typedefs, such as ``ULString``.

    Because the CFFI type object doesn't provide this information directly, the approach
    here is to build a *reverse* typedef mapping from the parsed declarations, to keep
    track of which typedefs refer to which CFFI type objects.  It's a reverse mapping in
    the sense that the CFFI parser's ``_declarations`` maps typedef names to type
    objects, whereas this goes the opposite direction.

    A tricky implementation detail is that the mapping needs to be keyed by type object
    **ID** rather than the reference to the object itself, because multiple type objects
    may have the same exact signature and be equivalent according to the ``==``
    operator, but we really need to track the exact object reference (i.e. matching in
    terms of the ``is`` operator) in order to disambiguate which typedef the type object
    was generated from.
    """

    typedef_map: _TypedefMap = {}
    for type_name, (type_obj, _) in declarations.items():
        assert isinstance(type_obj, cffi.model.BaseTypeByIdentity)
        if type_name.startswith('typedef '):
            type_id = id(type_obj)

            aliases: set[str]
            if type_id not in typedef_map:
                aliases = set()
                typedef_map[type_id] = (type_obj, aliases)
            else:
                existing_obj, aliases = typedef_map[type_id]
                assert existing_obj is type_obj

            alias = type_name.removeprefix('typedef ')
            aliases.add(alias)

    return typedef_map


def _find_typedef_alias(
    typedef_map: _TypedefMap,
    type_obj: cffi.model.BaseTypeByIdentity,
) -> str | None:
    """Finds the unique typedef name alias that generated a particular CFFI type object.

    If multiple typedefs refer to the same type object, then it's considered to be
    ambiguous/non-unique, and thus ``None`` is returned.
    """
    alias: str | None
    type_id = id(type_obj)
    if type_id in typedef_map:
        existing_obj, aliases = typedef_map.get(type_id)
        assert existing_obj is type_obj
        alias = next(iter(aliases)) if len(aliases) == 1 else None
    else:
        alias = None
    return alias


def _transform_function_ptr(
    typedef_map: _TypedefMap,
    type_obj: cffi.model.BaseTypeByIdentity,
) -> str:
    arg_defs: list[str] = []
    for arg_index, arg_type_obj in enumerate(type_obj.args):
        arg_typename = _transform_field_typename(typedef_map, arg_type_obj)
        arg_defs.append(arg_typename)
    arg_def_text = ', '.join(arg_defs)
    return_typename = _transform_field_typename(typedef_map, type_obj.result)
    return f'Callable[[{arg_def_text}], {return_typename}]'


def _transform_field_typename(
    typedef_map: _TypedefMap,
    type_obj: cffi.model.BaseTypeByIdentity,
) -> str:
    result: str

    if (alias := _find_typedef_alias(typedef_map, type_obj)) is not None:
        result = alias

    elif isinstance(type_obj, cffi.model.VoidType):
        result = 'None'

    elif isinstance(type_obj, cffi.model.PointerType):
        if isinstance(type_obj.totype, cffi.model.VoidType):
            result = 'Any'
        elif (
            isinstance(type_obj.totype, cffi.model.PrimitiveType)
            and type_obj.totype.name == 'char'
        ):
            result = 'bytes'
        else:
            to_typename = _transform_field_typename(typedef_map, type_obj.totype)
            result = f'Pointer[{to_typename}]'

    elif isinstance(type_obj, cffi.model.StructType):
        result = type_obj.name

    elif isinstance(type_obj, cffi.model.PrimitiveType):
        if type_obj.name == '_Bool':
            result = 'bool'
        elif type_obj.is_integer_type():  # type: ignore[no-untyped-call]
            result = 'int'
        elif type_obj.is_float_type():  # type: ignore[no-untyped-call]
            result = 'float'
        elif type_obj.is_char_type():  # type: ignore[no-untyped-call]
            result = 'bytes'
        else:
            raise NotImplementedError(
                f'Unsupported field type: {type(type_obj)} {type_obj}'
            )

    elif isinstance(type_obj, cffi.model.FunctionPtrType):
        result = _transform_function_ptr(typedef_map, type_obj)

    elif isinstance(type_obj, cffi.model.ArrayType):
        item_typename = _transform_field_typename(typedef_map, type_obj.item)
        result = f'Pointer[{item_typename}]'

    else:
        result = 'unknown'
        # breakpoint()

    return result


def _transform_struct_field(
    typedef_map: _TypedefMap,
    field_name: str,
    field_type: cffi.model.BaseTypeByIdentity,
) -> str:
    py_typename = _transform_field_typename(typedef_map, field_type)
    return f'{field_name}: {py_typename}'


def _transform_struct_typedef(
    typedef_map: _TypedefMap,
    type_name: str,
    type_obj: cffi.model.StructType,
) -> str:
    assert type_name.startswith('typedef ')
    name = type_name.removeprefix('typedef ')

    result = f'class {name}:\n'
    if type_obj.fldnames and type_obj.fldtypes:
        for field_name, field_type in zip(type_obj.fldnames, type_obj.fldtypes):
            field_def = _transform_struct_field(typedef_map, field_name, field_type)
            result += f'    {field_def}\n'
    else:
        result += '    ...\n'
    return result


def _transform_enum_typedef(
    typedef_map: _TypedefMap,
    type_name: str,
    type_obj: cffi.model.EnumType,
) -> str:
    assert type_name.startswith('typedef ')
    name = type_name.removeprefix('typedef ')

    result = f'class {name}(enum.IntEnum):\n'
    assert len(type_obj.enumerators) != 0 and len(type_obj.enumvalues) != 0
    for member_name, member_value in zip(type_obj.enumerators, type_obj.enumvalues):
        result += f'    {member_name} = {member_value}\n'
    result += '\n\n'

    # Also add top-level aliases:
    for member_name, member_value in zip(type_obj.enumerators, type_obj.enumvalues):
        result += f'{member_name} = {name}.{member_name}\n'

    result += '\n'
    return result


def _transform_function_type(
    typedef_map: _TypedefMap,
    type_name: str,
    type_obj: cffi.model.FunctionPtrType,
) -> str:
    assert type_name.startswith('function ')
    func_name = type_name.removeprefix('function ')

    arg_names_text = ''
    arg_annotations_text = ''
    for arg_index, arg_type_obj in enumerate(type_obj.args):
        # Ideally the argument names would match the argument names in the C headers,
        # but the CFFI parser doesn't provide such information, so the arg names have to
        # just be `arg0`, `arg1`, etc.
        arg_name = f'arg{arg_index}'
        arg_names_text += arg_name + ', '
        arg_typename = _transform_field_typename(typedef_map, arg_type_obj)
        arg_annotations_text += f'{arg_name}: {arg_typename}, '

    if arg_annotations_text:
        # Ending the function argument list with `/` enforces that the arguments are
        # passed positionally - but only if there's at least one arg.
        arg_annotations_text += '/,'

    return_typename = _transform_field_typename(typedef_map, type_obj.result)
    ignore_return_type = (
        '# type: ignore[no-any-return]' if return_typename != 'Any' else ''
    )
    result = f'def {func_name}({arg_annotations_text}) -> {return_typename}:\n'
    result += (
        f'    return ({ignore_return_type}\n'
        f'        _base.get_lib().{func_name}(  # type: ignore[attr-defined]\n'
        f'            {arg_names_text}\n'
        '        )'
        '    )'
    )
    return result


def _transform_function_ptr_typedef(
    typedef_map: _TypedefMap,
    type_name: str,
    type_obj: cffi.model.FunctionPtrType,
) -> str:
    assert type_name.startswith('typedef ')
    name = type_name.removeprefix('typedef ')
    callable_text = _transform_function_ptr(typedef_map, type_obj)
    return f'{name}: TypeAlias = {callable_text}\n'


def _transform_declaration(
    typedef_map: _TypedefMap,
    type_name: str,
    type_obj: cffi.model.BaseTypeByIdentity,
) -> str:
    assert isinstance(type_obj, cffi.model.BaseTypeByIdentity)
    _logger.debug('declaration: %s %r %r', type_name, type(type_obj), type_obj)

    result: str

    if isinstance(type_obj, cffi.model.StructType):
        if type_name.startswith('typedef '):
            #
            # Example: `typedef struct { float value[4]; } ULvec4;` - where `ULvec4`
            # becomes `class ULvec4: ...` with actual field definitions.
            #
            result = _transform_struct_typedef(typedef_map, type_name, type_obj)

        elif type_name.startswith('anonymous '):
            #
            # Example: same as `typedef struct { float value[4]; } ULvec4;` - but the
            # "anonymous" portion is the inner `struct { float value[4]; }` only, which
            # is redundant and thus skipped.
            #
            alias = _find_typedef_alias(typedef_map, type_obj)
            result = ''  # f'# anonymous struct: {type_name}; alias: {alias}\n'

        elif type_name.startswith('struct '):
            #
            # Example: the inner part of `typedef struct C_String* ULString;` - i.e.
            # `struct C_String` needs to be declared as an empty `class C_String: ...`
            # so that the typedef for `ULString` can become `Pointer[C_String]`.
            #
            name = type_name.removeprefix('struct ')
            result = f'class {name}: ...\n'

        elif type_name.startswith('constant '):
            result = f'# constant: {type_name}\n'  # TODO?

        else:
            raise NotImplementedError(
                f'Unsupported struct: {type_name} {type(type_obj)} {type_obj}'
            )

    elif isinstance(type_obj, cffi.model.FunctionPtrType):
        if type_name.startswith('function '):
            result = _transform_function_type(typedef_map, type_name, type_obj)
        elif type_name.startswith('typedef '):
            result = _transform_function_ptr_typedef(typedef_map, type_name, type_obj)
        else:
            raise NotImplementedError(
                f'Unsupported function pointer: {type_name} {type(type_obj)} {type_obj}'
            )

    elif isinstance(type_obj, cffi.model.PrimitiveType):
        alias = _find_typedef_alias(typedef_map, type_obj)
        result = (
            ''  # f'# primitive type: {type_name}; {type(type_obj)}; alias: {alias}\n'
        )

    elif isinstance(type_obj, cffi.model.PointerType):
        if type_name.startswith('typedef '):
            name = type_name.removeprefix('typedef ')
            to_typename = _transform_field_typename(typedef_map, type_obj.totype)
            result = f'{name}: TypeAlias = Pointer[{to_typename}]'
        else:
            raise NotImplementedError(
                f'Unsupported pointer: {type_name} {type(type_obj)} {type_obj}'
            )

    elif isinstance(type_obj, cffi.model.EnumType):
        if type_name.startswith('typedef '):
            result = _transform_enum_typedef(typedef_map, type_name, type_obj)
        elif type_name.startswith('anonymous '):
            alias = _find_typedef_alias(typedef_map, type_obj)
            result = ''  # f'# anonymous enum: {type_name}; alias: {alias}\n'
        else:
            raise NotImplementedError(
                f'Unsupported pointer enum: {type_name} {type(type_obj)} {type_obj}'
            )

    else:
        alias = _find_typedef_alias(typedef_map, type_obj)
        # result = (
        #     f'# unknown obj: {type_name}; {type(type_obj)} {type_obj}; alias: {alias}\n'
        # )
        raise NotImplementedError(
            f'Unsupported type: {type_name} {type(type_obj)} {type_obj}; alias: {alias}'
        )

    return result


def _transform_declarations(
    declarations: dict[str, tuple[cffi.model.BaseTypeByIdentity, Any]]
) -> str:
    typedef_map = _get_typedef_map(declarations)

    result = dedent(
        '''\
        """
        WARNING: This file is generated automatically by ``scripts/_build.py``.
        Do not edit this file by hand!
        """

        import enum
        from collections.abc import Callable
        from typing import Any
        from typing import TypeAlias
        from ._base import Pointer
        from . import _base
        '''
    )
    for type_name, (type_obj, _) in declarations.items():
        if type_name not in _SKIP_DECL_NAMES:
            result += _transform_declaration(typedef_map, type_name, type_obj)
            result += '\n'
    return result


def create_ffibuilder() -> cffi.FFI:
    # _logger.setLevel(logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG)

    ffibuilder = cffi.FFI()
    ffibuilder.cdef(_SRC_DIR.joinpath('_bindings.h').read_text())
    ffibuilder.set_source('ultralight_cffi._bindings', None)  # type: ignore[arg-type]

    parser: cffi.cparser.Parser = ffibuilder._parser  # type: ignore[attr-defined,name-defined]
    text = _transform_declarations(parser._declarations)
    pathlib.Path('ultralight_cffi').joinpath('_stubs.py').write_text(text)
    return ffibuilder


if __name__ == '__main__':
    create_ffibuilder().compile(verbose=True)
