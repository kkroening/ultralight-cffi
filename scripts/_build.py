import pathlib
from cffi import FFI

_HERE = pathlib.Path(__file__).parent
_ROOT_DIR = _HERE.parent
_SRC_DIR = _ROOT_DIR / 'ultralight'


def create_ffibuilder():
    ffibuilder = FFI()
    ffibuilder.cdef(_SRC_DIR.joinpath('_cffi.h').read_text())
    ffibuilder.set_source('ultralight._cffi', None)
    return ffibuilder


if __name__ == '__main__':
    create_ffibuilder().compile(verbose=True)
