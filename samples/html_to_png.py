""":mod:`ultralight_cffi` example: Load HTML and render as PNG.

This is adapted from the official `Sample 1 - Render to PNG`_ and `Sample 4 -
Javascript`_ examples - originally written in C/C++.

Configure the ``ULTRALIGHT_LIB_PATH`` environment variable, or place link the
Ultralight SDK into ``sdk/`` of the current working directory, so that the
shared libraries show up in ``sdk/bin``.

.. Sample 1 - Render to PNG:
    https://github.com/ultralight-ux/Ultralight/tree/master/samples

.. Sample 4 - Javascript:
    https://github.com/ultralight-ux/Ultralight/tree/master/samples
"""

import contextlib
import os
import pathlib
import time
import ultralight_cffi

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))

done = False


@ultralight_cffi.callback(
    'void(void*, struct C_View*, unsigned long long, _Bool, struct C_String*)'
)
def on_finish_loading(user_data, caller, frame_id, is_main_frame, url):
    global done
    if is_main_frame:
        print('Our page has loaded!')
        done = True


def main():
    global done

    lib = ultralight_cffi.load(_SDK_PATH / 'bin')

    sdk_path_str = lib.ulCreateStringUTF8(
        str(_SDK_PATH).encode(), len(str(_SDK_PATH).encode())
    )
    lib.ulEnablePlatformFileSystem(sdk_path_str)
    lib.ulDestroyString(sdk_path_str)
    lib.ulEnablePlatformFontLoader()

    config = lib.ulCreateConfig()
    renderer = lib.ulCreateRenderer(config)
    lib.ulDestroyConfig(config)

    view_config = lib.ulCreateViewConfig()
    view = lib.ulCreateView(renderer, 800, 600, view_config, ultralight_cffi.NULL)
    lib.ulDestroyViewConfig(view_config)

    with contextlib.ExitStack() as exit_stack:
        exit_stack.callback(lib.ulDestroyView, view)

        lib.ulViewSetFinishLoadingCallback(
            view, on_finish_loading, ultralight_cffi.NULL
        )

        print('Starting Run(), waiting for page to load...')

        html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
        html_str = lib.ulCreateStringUTF8(html, len(html))
        lib.ulViewLoadHTML(view, html_str)
        lib.ulDestroyString(html_str)

        while not done:
            lib.ulUpdate(renderer)
            time.sleep(0.01)

        lib.ulRender(renderer)
        surface = lib.ulViewGetSurface(view)
        bitmap = lib.ulBitmapSurfaceGetBitmap(surface)

        out_filename = 'result.png'
        lib.ulBitmapWritePNG(bitmap, out_filename.encode())

        print(f'Saved a render of our page to {out_filename}.')


if __name__ == '__main__':
    main()
