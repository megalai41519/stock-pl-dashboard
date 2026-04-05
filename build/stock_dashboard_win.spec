# build/stock_dashboard_win.spec
# Run from project root: pyinstaller build\stock_dashboard_win.spec

import sys
import os

block_cipher = None

# Always resolve paths relative to this spec file — works from any working directory
SPEC_DIR    = os.path.dirname(os.path.abspath(SPEC))          # .../build/
ROOT_DIR    = os.path.dirname(SPEC_DIR)                        # .../stock-pl-dashboard/
MAIN_PY     = os.path.join(ROOT_DIR, 'main.py')
FRONTEND    = os.path.join(ROOT_DIR, 'frontend')

a = Analysis(
    [MAIN_PY],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        (FRONTEND, 'frontend'),
    ],
    hiddenimports=[
        'app',
        'app.config',
        'app.data',
        'app.data.loader',
        'app.data.fetcher',
        'app.data.cache',
        'app.analytics',
        'app.analytics.pnl',
        'app.routes',
        'app.routes.portfolio',
        'app.routes.charts',
        'app.routes.news',
        'fastapi',
        'fastapi.routing',
        'fastapi.responses',
        'fastapi.staticfiles',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.staticfiles',
        'starlette.responses',
        'starlette.requests',
        'uvicorn',
        'uvicorn.main',
        'uvicorn.config',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'anyio',
        'anyio.streams',
        'anyio.streams.memory',
        'h11',
        'httptools',
        'websockets',
        'pydantic',
        'pydantic.deprecated.class_validators',
        'multipart',
        'dotenv',
        'yfinance',
        'pandas',
        'requests',
        'sqlite3',
        'json',
        # Windows-specific
        'win32api',
        'win32con',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # UI / viz not needed at runtime
        'tkinter', 'matplotlib', 'notebook', 'IPython',
        # Test infrastructure — never bundle into the app
        'pytest', '_pytest', 'pytest_asyncio',
        'unittest', 'doctest',
        # Dev tools
        'pdb', 'profile', 'cProfile', 'timeit',
        'setuptools', 'pip', 'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StockDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no CMD window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
