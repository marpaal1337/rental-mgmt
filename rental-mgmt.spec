# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for rental-mgmt (onedir mode).

Produces dist/rental-mgmt/ — directory with EXE + all dependencies.
"""
from PyInstaller.utils.hooks import collect_data_files

import os
import platform
from pathlib import Path

BASE_DIR = Path(SPECPATH).resolve()

datas = [
    (str(BASE_DIR / "frontend" / "dist" / "assets"), "frontend/dist/assets"),
    (str(BASE_DIR / "frontend" / "dist" / "index.html"), "frontend/dist"),
    (str(BASE_DIR / "alembic"), "alembic"),
    (str(BASE_DIR / "alembic.ini"), "."),
]
datas += collect_data_files("alembic")
datas += collect_data_files("sqlmodel")

binaries = []
if platform.system() == "Linux":
    libpython = "/usr/lib/x86_64-linux-gnu/libpython3.12.so.1"
    if os.path.exists(libpython):
        binaries.append((libpython, "."))

hidden_imports = [
    "alembic", "alembic.config", "alembic.command", "alembic.util",
    "sqlmodel",
    "uvicorn", "uvicorn.loggers", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websocket", "uvicorn.protocols.websocket.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on", "uvicorn.logging",
    "uvicorn.workers", "uvicorn.supervisors",
    "uvicorn.supervisors.multiprocess", "uvicorn.supervisors.watchfilesreload",
    "fastapi", "fastapi.openapi", "fastapi.openapi.utils", "fastapi.staticfiles",
    "starlette", "starlette.middleware", "starlette.staticfiles",
    "starlette.exceptions", "starlette.responses",
    "pydantic", "pydantic.fields",
    "yaml",
    "webview", "webview.js",
    "apscheduler", "apscheduler.triggers", "apscheduler.triggers.cron",
    "apscheduler.triggers.interval", "apscheduler.schedulers",
    "apscheduler.schedulers.background",
    "reportlab", "reportlab.lib", "reportlab.platypus", "reportlab.pdfgen",
    "dotenv", "multipart",
]

a = Analysis(
    ["desktop.py"],
    pathex=[str(BASE_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rental-mgmt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="rental-mgmt",
)
