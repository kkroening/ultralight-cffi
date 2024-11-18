import contextlib
import os
import pathlib
import ultralight_cffi

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))


def main() -> None:
    global done

    lib = ultralight_cffi.load(_SDK_PATH / 'bin')

    with contextlib.ExitStack() as exit_stack:
        sdk_path_str = lib.ulCreateStringUTF8(
            str(_SDK_PATH).encode(), len(str(_SDK_PATH).encode())
        )
        exit_stack.callback(lib.ulDestroyString, sdk_path_str)
        lib.ulEnablePlatformFileSystem(sdk_path_str)
        lib.ulEnablePlatformFontLoader()

        config = lib.ulCreateConfig()
        exit_stack.callback(lib.ulDestroyConfig, config)
        settings = lib.ulCreateSettings()
        exit_stack.callback(lib.ulDestroySettings, settings)
        app = lib.ulCreateApp(settings, config)
        exit_stack.callback(lib.ulDestroyApp, app)

        width = 900
        height = 600
        monitor = lib.ulAppGetMainMonitor(app)
        window = lib.ulCreateWindow(
            monitor, width, height, False, lib.kWindowFlags_Titled
        )
        exit_stack.callback(lib.ulDestroyWindow, window)
        lib.ulWindowSetTitle(window, 'ultralight-cffi Sample - Basic App'.encode())

        win_width = lib.ulWindowGetWidth(window)
        win_height = lib.ulWindowGetHeight(window)
        overlay = lib.ulCreateOverlay(window, win_width, win_height, 0, 0)
        exit_stack.callback(lib.ulDestroyOverlay, window)

        view = lib.ulOverlayGetView(overlay)
        html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
        html_obj = lib.ulCreateStringUTF8(html, len(html))
        exit_stack.callback(lib.ulDestroyString, html_obj)
        lib.ulViewLoadHTML(view, html_obj)

        def handle_error(exc_type, exc_value, exc_traceback):
            print(f'CFFI callback exception {exc_type}: {exc_value!r}')
            if exc_type is not None:
                lib.ulAppQuit(app)

        @ultralight_cffi.ffi.callback('void(void*)', onerror=handle_error)
        def on_update(user_data):
            pass

        @ultralight_cffi.ffi.callback('void(void*, struct C_Window*)')
        def on_close(user_data, window):
            print('on_close', user_data, window)
            lib.ulAppQuit(app)

        lib.ulAppSetUpdateCallback(app, on_update, ultralight_cffi.NULL)
        lib.ulWindowSetCloseCallback(window, on_close, ultralight_cffi.NULL)

        print('Starting...')
        try:
            lib.ulAppRun(app)
        finally:
            # WARNING: Ultralight apparently completely destroys the entire process at
            # the end of its event loop, so `ulAppRun()` never actually returns.  It
            # doesn't matter if you surround it with `try`/`finally` - it's a
            # catastrophically hard process termination that seems to make it impossible
            # to do proper cleanup in any reasonable manner.
            #
            # The ExitStack in this example is done in such a way that if Ultralight
            # ever fixes this issue in the future so that `ulAppRun` doesn't kill the
            # process, the ExitStack should just do the right thing.
            #
            # See https://github.com/ultralight-ux/Ultralight/issues/478
            print('Shutting down...')


if __name__ == '__main__':
    main()
