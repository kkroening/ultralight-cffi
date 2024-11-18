import ultralight_cffi


def test__sample__html_to_png(lib, sdk_init):
    config = lib.ulCreateConfig()
    renderer = lib.ulCreateRenderer(config)
    lib.ulDestroyConfig(config)

    view_config = lib.ulCreateViewConfig()
    lib.ulViewConfigSetInitialDeviceScale(view_config, 2.0)
    lib.ulViewConfigSetIsAccelerated(view_config, False)
    view = lib.ulCreateView(renderer, 400, 400, view_config, ultralight_cffi.NULL)
    lib.ulDestroyViewConfig(view_config)

    print('Starting Run(), waiting for page to load...')

    html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
    html_obj = lib.ulCreateStringUTF8(html, len(html))
    lib.ulViewLoadHTML(view, html_obj)
    lib.ulDestroyString(html_obj)

    lib.ulUpdate(renderer)
    lib.ulRender(renderer)
    surface = lib.ulViewGetSurface(view)
    bitmap = lib.ulBitmapSurfaceGetBitmap(surface)

    out_filename = 'result2.png'
    lib.ulBitmapWritePNG(bitmap, out_filename.encode())

    print(f'Saved a render of our page to {out_filename}.')
