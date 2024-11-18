from setuptools import setup

setup(
    author='Karl Kroening',
    author_email='karlk@kralnet.us',
    # cffi_modules=['scripts/_build.py:create_ffibuilder'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
    ],
    description='Ultralight CFFI bindings',
    install_requires=['cffi>=1.0.0'],
    license='Apache',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    name='ultralight_cffi',
    packages=['ultralight'],
    setup_requires=['cffi>=1.0.0'],
    url='https://github.com/kkroening/ultralight-cffi',
    version='0.1.0',
)
