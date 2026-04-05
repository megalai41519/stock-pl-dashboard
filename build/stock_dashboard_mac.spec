# build/stock_dashboard_mac.spec
# Run from project root: pyinstaller build/stock_dashboard_mac.spec

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
        # App modules
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
        # FastAPI / Starlette internals
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
        # Uvicorn
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
        # Data / networking
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
    [],
    exclude_binaries=True,
    name='StockDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # no terminal window
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockDashboard',
)

app = BUNDLE(
    coll,
    name='StockDashboard.app',
    icon=None,
    bundle_identifier='com.stockdashboard.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
        'CFBundleShortVersionString': '1.0.0',
    },
)
