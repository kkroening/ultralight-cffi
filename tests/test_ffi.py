import mock
import pathlib
import ultralight_cffi as ultra
from . import BIN_PATH


def test_load__patched(mocker):
    """Tests :meth:`ultralight.load` with the ``dlopen`` calls patched out."""
    dlopen_mock = mocker.patch.object(
        ultra._ffi,
        'ffi',
        dlopen=mock.Mock(
            side_effect=lambda name: mock.Mock(_name=name),
        ),
    )
    lib = ultra.load()

    # Scenario - library_path default:
    expected_lib_names = ultra._ffi._get_library_names()
    assert lib._name == expected_lib_names[-1]
    dlopen_mock.call_args_list == [
        mock.call(lib_name) for lib_name in expected_lib_names
    ]
    dlopen_mock.reset_mock()

    # Scenario - library_path str:
    lib_path_str = 'some/dir'
    lib = ultra.load(lib_path_str)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    dlopen_mock.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    dlopen_mock.reset_mock()

    # Scenario - library_path path:
    lib_path = pathlib.Path(lib_path_str)
    lib = ultra.load(lib_path)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    dlopen_mock.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    dlopen_mock.reset_mock()


def test_load():
    lib = ultra.load(BIN_PATH)
    assert isinstance(lib, ultra.Lib)
