import contextlib
import os
import pathlib
import time
import ultralight_cffi
from typing import Any

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))

done = False


@ultralight_cffi.callback(
    'void(void*, struct C_View*, unsigned long long, _Bool, struct C_String*)'
)
def on_finish_loading(
    user_data: ultralight_cffi.CData,
    caller: Any,
    frame_id: Any,
    is_main_frame: Any,
    url: Any,
) -> None:
    global done  # pylint: disable=global-statement
    if is_main_frame:
        print('Our page has loaded!')
        done = True


def main() -> None:
    ultralight_cffi.load(_SDK_PATH / 'bin')

    sdk_path_str = ultralight_cffi.ulCreateStringUTF8(
        str(_SDK_PATH).encode(), len(str(_SDK_PATH).encode())
    )
    ultralight_cffi.ulEnablePlatformFileSystem(sdk_path_str)
    ultralight_cffi.ulDestroyString(sdk_path_str)
    ultralight_cffi.ulEnablePlatformFontLoader()

    config = ultralight_cffi.ulCreateConfig()
    renderer = ultralight_cffi.ulCreateRenderer(config)
    ultralight_cffi.ulDestroyConfig(config)

    view_config = ultralight_cffi.ulCreateViewConfig()
    view = ultralight_cffi.ulCreateView(
        renderer, 800, 600, view_config, ultralight_cffi.NULL
    )
    ultralight_cffi.ulDestroyViewConfig(view_config)

    with contextlib.ExitStack() as exit_stack:
        exit_stack.callback(ultralight_cffi.ulDestroyView, view)

        ultralight_cffi.ulViewSetFinishLoadingCallback(
            view, on_finish_loading, ultralight_cffi.NULL
        )

        print('Starting Run(), waiting for page to load...')

        html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
        html_str = ultralight_cffi.ulCreateStringUTF8(html, len(html))
        ultralight_cffi.ulViewLoadHTML(view, html_str)
        ultralight_cffi.ulDestroyString(html_str)

        while not done:
            ultralight_cffi.ulUpdate(renderer)
            time.sleep(0.01)

        ultralight_cffi.ulRender(renderer)
        surface = ultralight_cffi.ulViewGetSurface(view)
        bitmap = ultralight_cffi.ulBitmapSurfaceGetBitmap(surface)

        out_filename = 'result.png'
        ultralight_cffi.ulBitmapWritePNG(bitmap, out_filename.encode())

        print(f'Saved a render of our page to {out_filename}.')


if __name__ == '__main__':
    main()
