""":mod:`ultralight_cffi` example: Custom surface implementation, using the
:class:`ultralight_cffi.CustomSurface` abstraction layer.
"""

import os
import pathlib
import PIL
import ultralight_cffi
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Self
from typing_extensions import Buffer

_SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))


@dataclass
class MemorySurface(ultralight_cffi.CustomSurface):
    width: int
    height: int
    pixels: bytearray = field(init=False, repr=False)
    row_bytes: int = field(init=False)
    _handle: Any = field(default=None, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.row_bytes = self.width * 4  # Assume BGRA 32-bit format (4 bytes per pixel)
        self.pixels = bytearray(self.row_bytes * self.height)

    @classmethod
    def create(cls, width: int, height: int) -> Self:
        return cls(width, height)

    def destroy(self) -> None:
        print(f'Destroying MemorySurface: {self}')
        # No special cleanup needed for this simple implementation

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def get_size(self) -> int:
        return len(self.pixels)

    def get_row_bytes(self) -> int:
        return self.row_bytes

    def lock_pixels(self) -> Buffer:
        print(f'Locking pixels for MemorySurface: {self}')
        return self.pixels

    def unlock_pixels(self) -> None:
        print(f'Unlocking pixels for MemorySurface: {self}')

    def resize(self, width: int, height: int) -> None:
        print(
            f'Resizing MemorySurface from {self.width}x{self.height} to {width}x{height}'
        )
        self.width = width
        self.height = height
        self.row_bytes = self.width * 4
        self.pixels = bytearray(self.row_bytes * self.height)

    def save_as_png(self, filename: str):
        width = self.get_width()
        height = self.get_height()
        row_bytes = self.get_row_bytes()
        try:
            pixels = self.lock_pixels()

            # Convert BGRA to RGBA (swap red and blue channels)
            rgba_pixels = bytearray(width * height * 4)
            for y in range(height):
                for x in range(width):
                    i = (y * row_bytes) + (x * 4)
                    rgba_pixels[i : i + 4] = [
                        pixels[i + 2],  # R
                        pixels[i + 1],  # G
                        pixels[i + 0],  # B
                        pixels[i + 3],  # A
                    ]

            # Create an Image object and save as PNG
            img = PIL.Image.frombytes('RGBA', (width, height), bytes(rgba_pixels))
            img.save(filename)
            print(f'Saved render to {filename}.')
        finally:
            self.unlock_pixels()


def _main():
    lib = ultralight_cffi.load(_SDK_PATH / 'bin')

    sdk_path_str = lib.ulCreateStringUTF8(
        str(_SDK_PATH).encode(), len(str(_SDK_PATH).encode())
    )
    lib.ulEnablePlatformFileSystem(sdk_path_str)
    lib.ulDestroyString(sdk_path_str)
    lib.ulEnablePlatformFontLoader()

    lib.ulPlatformSetSurfaceDefinition(MemorySurface.get_definition()[0])

    config = lib.ulCreateConfig()
    renderer = lib.ulCreateRenderer(config)
    lib.ulDestroyConfig(config)

    view_config = lib.ulCreateViewConfig()
    view = lib.ulCreateView(renderer, 400, 400, view_config, ultralight_cffi.NULL)
    lib.ulDestroyViewConfig(view_config)

    try:
        print('Starting Run(), waiting for page to load...')

        html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
        html_obj = lib.ulCreateStringUTF8(html, len(html))
        lib.ulViewLoadHTML(view, html_obj)
        lib.ulDestroyString(html_obj)

        lib.ulUpdate(renderer)
        lib.ulRender(renderer)
        surface_ffi = lib.ulViewGetSurface(view)
        surface = MemorySurface.from_ffi(lib, surface_ffi)
        surface.save_as_png('result.png')
    finally:
        lib.ulDestroyView(view)


if __name__ == '__main__':
    _main()
