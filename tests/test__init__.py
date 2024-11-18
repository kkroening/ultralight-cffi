import mock
import os
import pathlib
import ultralight

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))
_BIN_PATH = _SDK_PATH / 'bin'


def test_load__patched(mocker):
    """Tests :meth:`ultralight.load` with the ``dlopen`` calls patched out."""
    mocker.patch.object(
        ultralight,
        'ffi',
        dlopen=mock.Mock(
            side_effect=lambda name: mock.Mock(_name=name),
        ),
    )
    lib = ultralight.load()

    # Scenario - library_path default:
    expected_lib_names = ultralight._get_library_names()
    assert lib._name == expected_lib_names[-1]
    ultralight.ffi.dlopen.call_args_list == [
        mock.call(lib_name) for lib_name in expected_lib_names
    ]
    ultralight.ffi.dlopen.reset_mock()

    # Scenario - library_path str:
    lib_path_str = 'some/dir'
    lib = ultralight.load(lib_path_str)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    ultralight.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    ultralight.ffi.dlopen.reset_mock()

    # Scenario - library_path path:
    lib_path = pathlib.Path(lib_path_str)
    lib = ultralight.load(lib_path)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    ultralight.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    ultralight.ffi.dlopen.reset_mock()


def test_load():
    lib = ultralight.load(_BIN_PATH)
    assert isinstance(lib, ultralight.Lib)
