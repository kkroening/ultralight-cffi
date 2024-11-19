# [Ultralight](https://ultralig.ht/) CFFI bindings (Python)

<img src="https://ultralig.ht/media/ul_logo.webp" alt="Ultralight Logo" width="30%"/>

_(Not an officially endorsed [Ultralight](https://ultralig.ht/) project)_

## Overview

This library provides low-level, minimalistic [CFFI](https://cffi.readthedocs.io/en/latest/overview.html)-based bindings for Ultralight.

It's extremely lightweight - one might even say _ultra_-lightweight ;)

`ultralight-cffi`'s job is to provide auto-generated, low-level CFFI bindings for Ultralight - with PEP 484 type annotations.

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

The following example demonstrates how to initialize `ultralight-cffi`, load some HTML, and render to a PNG file headlessly - based on [`samples/html_to_png.py`](samples/html_to_png.py).

#### Initialization:

```python
import os
import pathlib
import ultralight_cffi as ultra

sdk_path = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))
ultra.load(sdk_path / 'bin')

sdk_path_str = ultra.ulCreateStringUTF8(
    str(sdk_path).encode(), len(str(sdk_path).encode())
)
ultra.ulEnablePlatformFileSystem(sdk_path_str)
ultra.ulDestroyString(sdk_path_str)
ultra.ulEnablePlatformFontLoader()

config = ultra.ulCreateConfig()
renderer = ultra.ulCreateRenderer(config)
ultra.ulDestroyConfig(config)

view_config = ultra.ulCreateViewConfig()
view = ultra.ulCreateView(renderer, 800, 600, view_config, ultra.NULL)
ultra.ulDestroyViewConfig(view_config)
```

> [!NOTE]
> The tedious string manipulation above (`ultra.ulCreateStringUTF8`, etc.) deserves a helper function in the future.

#### Setup `OnFinishLoading` callback:

```python
done = False

@ultra.callback(
    'void(void*, struct C_View*, unsigned long long, _Bool, struct C_String*)'
)
def on_finish_loading(user_data, caller, frame_id, is_main_frame, url):
    global done  # (non-Pythonic, but from the official example :)
    if is_main_frame:
        print('Our page has loaded!')
        done = True

ultra.ulViewSetFinishLoadingCallback(view, on_finish_loading, ultra.NULL)
```

#### Load HTML:

```python
html = '<html><body><h1>Hello, World!</h1></body></html>'.encode()
html_str = ultra.ulCreateStringUTF8(html, len(html))
ultra.ulViewLoadHTML(view, html_str)

print('Starting Run(), waiting for page to load...')

while not done:
    ultra.ulUpdate(renderer)
    time.sleep(0.01)
```

#### Render to PNG file:

```python
ultra.ulRender(renderer)
surface = ultra.ulViewGetSurface(view)
bitmap = ultra.ulBitmapSurfaceGetBitmap(surface)

out_filename = 'result.png'
ultra.ulBitmapWritePNG(bitmap, out_filename.encode())

print(f'Saved a render of our page to {out_filename}.')
```

## Usage

### Annotation layer vs raw CFFI interface

Type annotations for `ultralight_cffi.*` are automatically generated from the Ultralight API C header files.  CFFI itself does not provide type annotations, but a custom [script](scripts/_build.py) fills them in by generating annotated wrapper methods (in `ultralight_cffi/_stubs.py`) that delegate to the lower-level FFI bindings.

Annotations help catch and prevent mistakes like the following:

```python
bitmap = ultralight_cffi.ulBitmapSurfaceGetBitmap(view)  # incorrect!
```

In this example, the static type checker (e.g. mypy) quickly points out the fact that a _surface_ must be passed rather than a _view_:

```
error: Argument 1 to "ulBitmapSurfaceGetBitmap" has incompatible type "Pointer[C_View]"; expected "Pointer[C_Surface]"  [arg-type]
```

A quick change gets you back in business:

```python
bitmap = ultralight_cffi.ulBitmapSurfaceGetBitmap(surface)  # correct!
```

Once you embrace static typing in Python, it's hard to ever want to go back.

Nonetheless, if you're not using a type checker, you can ignore the annotations, since it's ultimately still just CFFI.  If you encounter issues with the annotation layer, you may wish to bypass it and call the raw FFI bindings directly:

```python
lib = ultralight_cffi.get_lib()
bitmap = lib.ulBitmapSurfaceGetBitmap(surface)  # equivalent to above, but without static typing
```

> [!NOTE]
> CFFI provides only a non-generic `FFI.CData` for everything, which makes it challenging to enforce typing statically.  `Pointer[_T]` is really just an alias for `FFI.CData` during type checking, and goes away at runtime.

### Examples

See the [`samples/`](./samples/) directory for various examples, including headless HTML rendering, custom `Surface` implementation, etc.

## Development

### Repo structure

This library consists of an `ultralight_cffi` Python package, which has a thin wrapper around an auto-generated `ultralight_cffi/_cffi.py`:

```
├── ultralight-api/         Official Ultralight-API headers, as a git submodule
│
├── ultralight_cffi/        The main Python library source code
│   ├── __init__.py         Wrapper module
│   ├── _bindings.h         Auto-generated Ultralight preprocessed headers
│   ├── _bindings.py        Auto-generated Ultralight CFFI bindings
│   ├── _stubs.py           Auto-generated PEP 484 annotation layer
│   └──  ...                etc.
│
├── scripts/
│   ├── _build.py           Runs CFFI builder
│   ├── ci                  Runs tests, mypy, pylint, etc. - same as GHA CI, but local
│   ├── fetch_sdk           Fetches the Ultralight SDK (experimental/development-only!)
│   └── gen_bindings        Re-generates `ultralight_cffi/_bindings.*` + `_stubs.py`
│
├── README.md               Where you are right now
├── pyproject.toml          Poetry-based package definitions/settings
│
```

The Ultralight-API headers are fetched as a git submodule for local development of this library, but are not required for end-user installation of `ultralight-cffi`.

`scripts/gen_bindings` transforms the official headers into a consolidated `ultralight_cffi/_bindings.h` using `gcc`'s preprocessor (running in Docker, for consistency), and a small amount of post-processing.  Then it runs `scripts/_build.py` to run the CFFI builder to generate `_bindings.py`.  And finally, `ultralight_cffi/_stubs.py` is generated by transforming the FFI builder's parsed declarations into PEP 484 annotated Python wrapper methods.

Although `ultralight/_bindings.*` and `ultralight/_stubs.py` are auto-generated, they're committed to version control so that installing `ultralight-cffi` is as frictionless as possible.

> [!NOTE]
> `ultralight/_bindings.h` isn't required at runtime, but it's included in the `ultralight` Python package anyways for the sake of documentation and history.

CFFI's _[Out-of-line, ABI level](https://cffi.readthedocs.io/en/latest/overview.html#out-of-line-abi-level)_ mode (rather than API mode) is used because it avoids the need to have the Ultralight shared libraries available for the distribution and installation of this library, which avoids the massive can of worms for maintaining platform-specific releases and dealing with licensing gotchas.  Although it may be appealing to be able to simply `pip install` this package and have everything magically work, it would guarantee that this package is broken 99.99% of the time.  On the other hand, having this library deal only with the CFFI binding generation makes the surface area of this library minuscule, and easier to maintain and fork - or at least serve as an example.

### Re-generating the bindings

> [!NOTE]
> End users don't need to re-generate the bindings, since `ultralight-cffi` can just be installed as-is.

#### Fetch `ultralight-api` directory (header files):

```bash
git submodule update --init
```

#### Generate `_ultralight/_bindings.*` and `_ultralight/_stubs.py`:

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

The auto-generated bindings + stubs are committed with the repo to be included directly in the resulting Python package:

```bash
git add ultralight_cffi/_bindings.* ultralight_cffi/_stubs.py
poetry version x.x.x
git commit -m 'Re-generate bindings'
git tag x.x.x
git push origin HEAD x.x.x
```

The updated bindings are then installable as a pip/Poetry-installable, git dependency, without any additional downstream build/extension tooling required for installation (besides `cffi` itself as a transitive dependency).
