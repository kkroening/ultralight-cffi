# Ultralight CFFI bindings

## Overview

This library provides low-level, minimalistic [CFFI](https://cffi.readthedocs.io/en/latest/overview.html)-based bindings for [Ultralight](https://ultralig.ht/).

It's extremely lightweight - one might even say _ultra_-lightweight ;)

This library's sole job is to provide auto-generated, low-level CFFI bindings for Ultralight.

**`ultralight-cffi` does not install Ultralight itself**.  It's up to you to provide the appropriate shared libraries at runtime, as redistribution of Ultralight is out of scope for this project.

## Installation

Below is a non-exhaustive set of installation methods for `ultralight-cffi`.

### Install from GitHub

#### Via `pip`:

```bash
pip install git+ssh://git@github.com/kkroening/ultralight-cffi
```

#### Via Poetry:

```bash
poetry add git+ssh://git@github.com/kkroening/ultralight-cffi
```

### Install from local fork

#### Via `pip` (editable mode):

```bash
git clone ssh://git@github.com/kkroening/ultralight-cffi
pip install -e ultralight-cffi
```

## Quickstart

The following example demonstrates how to initialize `ultralight-cffi`, load some HTML, and render to a PNG file headlessly.

#### Initialization:

```python
import os
import pathlib
import ultralight

sdk_path = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))
lib = ultralight.load(sdk_path / 'bin')

sdk_path_str = lib.ulCreateStringUTF8(
    str(sdk_path).encode(), len(str(sdk_path).encode())
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
view = lib.ulCreateView(renderer, 1600, 800, view_config, ultralight.ffi.NULL)
lib.ulDestroyViewConfig(view_config)
```

> [!NOTE]
> The tedious string manipulation above (`lib.ulCreateStringUTF8`, etc.) deserves a helper function in the future.

#### Setup `OnFinishLoading` callback:

```python
done = False

@ultralight.ffi.callback(
    'void(void*, struct C_View*, unsigned long long, _Bool, struct C_String*)'
)
def on_finish_loading(user_data, caller, frame_id, is_main_frame, url):
    global done  # (non-Pythonic, but from the official example :)
    if is_main_frame:
        print('Our page has loaded!')
        done = True

lib.ulViewSetFinishLoadingCallback(view, on_finish_loading, ultralight.ffi.NULL)
```

#### Load HTML:

```python
html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
html_str = lib.ulCreateStringUTF8(html, len(html))
lib.ulViewLoadHTML(view, html_str)

print('Starting Run(), waiting for page to load...')

while not done:
    lib.ulUpdate(renderer)
    time.sleep(0.01)
```

#### Render to PNG file:

```python
lib.ulRender(renderer)
surface = lib.ulViewGetSurface(view)
bitmap = lib.ulBitmapSurfaceGetBitmap(surface)

out_filename = 'result.png'
lib.ulBitmapWritePNG(bitmap, out_filename.encode())

print(f'Saved a render of our page to {out_filename}.')
```

See [`samples/html_to_png.py`](samples/html_to_png.py).

## Development

### Repo structure

This library consists of an `ultralight` Python package, which has a thin wrapper around an auto-generated `ultralight/_cffi.py`:

```
├── ultralight-api/         Official Ultralight-API headers, as a git submodule
│
├── ultralight/             The main Python library source code
│   ├── __init__.py         Wrapper module
│   ├── _cffi.h             Auto-generated Ultralight preprocessed headers
│   ├── _cffi.py            Auto-generated Ultralight CFFI bindings
│   └──  ...                Additional wrapper logic
│
├── scripts/
│   ├── _build.py           Runs CFFI builder
│   ├── ci                  Runs tests, mypy, pylint, etc. - same as GHA CI, but local
│   ├── fetch_sdk           Fetches the Ultralight SDK (experimental/development-only!)
│   └── gen_bindings        Re-generates `ultralight/_cffi.*`
│
├── README.md               Where you are right now
├── pyproject.toml          Poetry-based package definitions/settings
│
```

The Ultralight-API headers are fetched as a git submodule for local development of this library, but are not required for end-user installation of `ultralight-cffi`.

`scripts/gen_bindings` transforms the official headers into a consolidated `ultralight/_cffi.h` using `gcc`'s preprocessor (running in Docker, for consistency), and a small amount of post-processing.  Then it runs `scripts/_build.py` to run the CFFI builder to generate `_cffi.py`.

Although `ultralight/_cffi.h` and `ultralight/_cffi.py` are auto-generated, they're committed to version control so that installing `ultralight-cffi` is as frictionless as possible.

> [!NOTE]
> `ultralight/_cffi.h` isn't required at runtime, but it's included in the `ultralight` Python package anyways for the sake of documentation and history.

CFFI's _[Out-of-line, ABI level](https://cffi.readthedocs.io/en/latest/overview.html#out-of-line-abi-level)_ mode (rather than API mode) is used because it avoids the need to have the Ultralight shared libraries available for the distribution and installation of this library, which avoids the massive can of worms for maintaining platform-specific releases and dealing with licensing gotchas.  Although it may be appealing to be able to simply `pip install` this package and have everything magically work, it would guarantee that this package is broken 99.99% of the time.  On the other hand, having this library deal only with the CFFI binding generation makes the surface area of this library minuscule, and easier to maintain and fork - or at least serve as an example.

### Re-generating the bindings

> [!NOTE]
> End users don't need to re-generate the bindings, since `ultralight-cffi` can just be installed as-is.

#### Fetch `ultralight-api` directory (header files):

```bash
git submodule update --init
```

#### Generate `_ultralight/_cffi.h` and `_ultralight/_cffi.py`:

```bash
./scripts/gen_bindings
```

#### Run tests, mypy, pylint, etc.:

```bash
./scripts/ci
```

> [!NOTE]
> In addition to the Ultralight-API headers submodule, `scripts/ci` _also_ fetches the SDK (via `scripts/fetch_sdk`) which is seemingly redundant.  However, the SDK download is a weak reference to a somewhat unreliable 7z download URL and is only used for testing, whereas the submodule is pinned to a specific git hash as a stronger reference to ensure deterministic CFFI binding code generation.

#### Commit and release:

```bash
git add ultralight/_cffi.*
poetry version x.x.x
git commit -m 'Re-generate bindings'
git tag x.x.x
git push origin HEAD x.x.x
```

The updated bindings are then installable downstream as a pip/Poetry-installable, git dependency.
