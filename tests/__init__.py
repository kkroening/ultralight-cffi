import os
import pathlib

SDK_PATH = pathlib.Path(os.environ.get('ULTRALIGHT_SDK_PATH', 'ultralight-sdk'))
BIN_PATH = SDK_PATH / 'bin'
