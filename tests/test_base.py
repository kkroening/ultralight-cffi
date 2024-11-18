import mock
import pathlib
from . import BIN_PATH
from ultralight_cffi import _base


def test_load__patched(mocker):
    """Tests :meth:`ultralight.load` with the ``dlopen`` calls patched out."""
    mocker.patch.object(
        _base,
        'ffi',
        dlopen=mock.Mock(
            side_effect=lambda name: mock.Mock(_name=name),
        ),
    )
    lib = _base.load()

    # Scenario - library_path default:
    expected_lib_names = _base._get_library_names()
    assert lib._name == expected_lib_names[-1]
    _base.ffi.dlopen.call_args_list == [
        mock.call(lib_name) for lib_name in expected_lib_names
    ]
    _base.ffi.dlopen.reset_mock()

    # Scenario - library_path str:
    lib_path_str = 'some/dir'
    lib = _base.load(lib_path_str)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    _base.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    _base.ffi.dlopen.reset_mock()

    # Scenario - library_path path:
    lib_path = pathlib.Path(lib_path_str)
    lib = _base.load(lib_path)
    assert lib._name == f'{lib_path_str}/{expected_lib_names[-1]}'
    _base.ffi.dlopen.call_args_list == [
        mock.call(f'{lib_path_str}/{lib_name}') for lib_name in expected_lib_names
    ]
    _base.ffi.dlopen.reset_mock()


def test_load():
    lib = _base.load(BIN_PATH)
    assert isinstance(lib, _base.Lib)
