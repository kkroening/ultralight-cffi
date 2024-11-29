import pytest
import ultralight_cffi as ultra
from . import SDK_PATH


@pytest.fixture()
def lib():
    return ultra.load(SDK_PATH / 'bin')


@pytest.fixture()
def sdk_init(lib):
    sdk_path_str = lib.ulCreateStringUTF8(
        str(SDK_PATH).encode(), len(str(SDK_PATH).encode())
    )
    lib.ulEnablePlatformFileSystem(sdk_path_str)
    lib.ulDestroyString(sdk_path_str)
    lib.ulEnablePlatformFontLoader()


@pytest.fixture()
def js_ctx(lib):
    with ultra.js_ctx.scoped_global() as ctx:
        yield ctx
