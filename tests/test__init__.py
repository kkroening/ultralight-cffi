import mock
import os
import pathlib
import ultralight_cffi

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))
_BIN_PATH = _SDK_PATH / 'bin'


def test_load__patched(mocker):
    """Tests :meth:`ultralight.load` with the ``dlopen`` calls patched out."""
    mocker.patch.object(
        ultralight_cffi,
        'ffi',
        dlopen=mock.Mock(
            side_effect=lambda name: mock.Mock(_name=name),
        ),
    )
    lib = ultralight_cffi.load()

    # Scenario - library_path default:
    expected_lib_names = ultralight_cffi._get_library_names()
    assert lib._name == expected_lib_names[-1]
    ultralight_cffi.ffi.dlopen.call_args_list == [
        mock.call(lib_name) for lib_name in expected_lib_names
    ]
    ultralight_cffi.ffi.dlopen.reset_mock()

    # Scenario - library_path str:
    lib_path_str = 'some/dir'
    lib = ultralight_cffi.load(lib_path_str)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    ultralight_cffi.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    ultralight_cffi.ffi.dlopen.reset_mock()

    # Scenario - library_path path:
    lib_path = pathlib.Path(lib_path_str)
    lib = ultralight_cffi.load(lib_path)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    ultralight_cffi.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    ultralight_cffi.ffi.dlopen.reset_mock()


def test_load():
    lib = ultralight_cffi.load(_BIN_PATH)
    assert isinstance(lib, ultralight_cffi.Lib)
