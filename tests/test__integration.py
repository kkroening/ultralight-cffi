import ultralight_cffi
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Self
from typing_extensions import Buffer


@dataclass
class MemorySurface(ultralight_cffi.CustomSurface):
    width: int
    height: int
    pixels: bytearray = field(init=False, repr=False)
    _handle: Any = field(default=None, init=False)

    locked: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        self.pixels = bytearray(self.width * self.height * 4)

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
        return self.width * 4

    def lock_pixels(self) -> Buffer:
        print(f'Locking pixels for MemorySurface: {self}')
        assert not self.locked
        self.locked = True
        return self.pixels

    def unlock_pixels(self) -> None:
        print(f'Unlocking pixels for MemorySurface: {self}')
        assert self.locked
        self.locked = False

    def resize(self, width: int, height: int) -> None:
        assert 0, 'should not be called for this test case'
        # print(
        #     f'Resizing MemorySurface from {self.width}x{self.height} to {width}x{height}'
        # )
        # self.width = width
        # self.height = height
        # self.row_bytes = self.width * 4
        # self.pixels = bytearray(self.row_bytes * self.height)


def test__custom_surface(lib, sdk_init):
    expected_width = 400
    expected_height = 300

    lib.ulPlatformSetSurfaceDefinition(MemorySurface.get_definition()[0])

    config = lib.ulCreateConfig()
    renderer = lib.ulCreateRenderer(config)
    lib.ulDestroyConfig(config)

    view_config = lib.ulCreateViewConfig()
    view = lib.ulCreateView(
        renderer, expected_width, expected_height, view_config, ultralight_cffi.NULL
    )
    lib.ulDestroyViewConfig(view_config)

    try:
        html = '<html><body style="background-color:#ff0000"><h1 style="color:#00ff00">Test</h1></body></html>'
        html_obj = lib.ulCreateStringUTF8(html.encode(), len(html))
        lib.ulViewLoadHTML(view, html_obj)
        lib.ulDestroyString(html_obj)

        # Render the view
        lib.ulUpdate(renderer)
        lib.ulRender(renderer)

        # Access the custom surface
        surface_ffi = lib.ulViewGetSurface(view)
        surface = MemorySurface.from_ffi(lib, surface_ffi)

        # Lock the surface and inspect the pixel buffer
        try:
            pixels = surface.lock_pixels()
            assert surface.width == expected_width
            assert surface.height == expected_height

            red_pixel = bytes([0x00, 0x00, 0xFF, 0xFF])  # Red background
            green_pixel = bytes([0x00, 0xFF, 0x00, 0xFF])  # Green text

            assert pixels[0:4] == red_pixel, 'Top-left pixel should be red'
            assert any(
                pixels[i : i + 4] == green_pixel for i in range(0, len(pixels), 4)
            ), 'Expected at least one green pixel in the buffer.'
        finally:
            # TODO: do better context management
            surface.unlock_pixels()

    finally:
        lib.ulDestroyView(view)
