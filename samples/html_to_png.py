"""Sample :mod:`ultralight_cffi` app: load HTML and render as PNG.

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

import os
import pathlib
import time
import ultralight_cffi
from textwrap import dedent

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))

_HTML = dedent(
    '''
    <html>
      <head>
        <style type="text/css">
          * { -webkit-user-select: none; }
          body {
            font-family: -apple-system, 'Segoe UI', Ubuntu, Arial, sans-serif;
            text-align: center;
            background: linear-gradient(#FFF, #DDD);
            padding: 2em;
          }
        </style>
      </head>
      <body>
        <h1>Hello, World!</h>
      </body>
    </html>
    '''
).encode('utf-8')

done = False


@ultralight_cffi.ffi.callback(
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
    lib.ulViewConfigSetInitialDeviceScale(view_config, 2.0)
    lib.ulViewConfigSetIsAccelerated(view_config, False)
    view = lib.ulCreateView(renderer, 1600, 800, view_config, ultralight_cffi.ffi.NULL)
    lib.ulDestroyViewConfig(view_config)

    lib.ulViewSetFinishLoadingCallback(
        view, on_finish_loading, ultralight_cffi.ffi.NULL
    )

    print('Starting Run(), waiting for page to load...')

    html_obj = lib.ulCreateStringUTF8(_HTML, len(_HTML))
    lib.ulViewLoadHTML(view, html_obj)

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
