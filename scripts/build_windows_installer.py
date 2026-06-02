"""Build a Windows installer for rental-mgmt.

Usage:
    python scripts/build_windows_installer.py           # Build InnoSetup .exe (default)
    python scripts/build_windows_installer.py --zip      # Build portable .zip only
    python scripts/build_windows_installer.py --wix      # Build WiX .msi only

Requirements (Windows):
    InnoSetup: https://jrsoftware.org/isdl.php (add iscc to PATH)
    WiX: https://wixtoolset.org (add candle, light, heat to PATH)

On WSL with InnoSetup installed on Windows:
    python scripts/build_windows_installer.py            # finds iscc.exe via /mnt/c/
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _find_windows_exe(name: str) -> str | None:
    """Find a Windows executable, checking WSL paths too."""
    exe = shutil.which(name)
    if exe:
        return exe
    name_lower = name.lower().removesuffix(".exe")
    for root in [Path("/mnt/c/Program Files (x86)"), Path("/mnt/c/Program Files")]:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() == ".exe" and p.stem.lower() == name_lower:
                return str(p)
    return None


def build_frontend():
    frontend_dist = BASE_DIR / "frontend" / "dist" / "index.html"
    if frontend_dist.exists():
        print("  Frontend already built, skipping...")
        return
    print("→ Building frontend...")
    frontend_dir = BASE_DIR / "frontend"
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(frontend_dir),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("ERROR building frontend:", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("  Frontend built successfully")


def build_innosetup():
    print("→ Building InnoSetup installer...")
    iscc = _find_windows_exe("iscc")
    if not iscc:
        print("  SKIP: iscc (InnoSetup compiler) not found.", file=sys.stderr)
        print("  Download from: https://jrsoftware.org/isdl.php", file=sys.stderr)
        return

    iss_file = BASE_DIR / "build" / "innosetup.iss"
    result = subprocess.run([iscc, str(iss_file)], cwd=str(BASE_DIR))
    if result.returncode != 0:
        print("ERROR building InnoSetup installer", file=sys.stderr)
        sys.exit(result.returncode)

    setups = list((BASE_DIR / "dist").glob("rental-mgmt-setup-*.exe"))
    if setups:
        print(f"  InnoSetup installer: {setups[0]}")
    else:
        print("  InnoSetup installer created in dist/")


def build_zip():
    print("→ Building portable ZIP bundle...")
    dist_dir = BASE_DIR / "dist"
    zip_path = dist_dir / "rental-mgmt-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        basedir = Path("rental-mgmt")
        for src, dst in [
            ("app", "app"),
            ("frontend/dist", "frontend/dist"),
            ("alembic", "alembic"),
            ("alembic.ini", "alembic.ini"),
            ("desktop.py", "desktop.py"),
            ("pyproject.toml", "pyproject.toml"),
            (".env.example", ".env.example"),
            ("data/db", "data/db"),
            ("data/backups", "data/backups"),
            ("data/invoices", "data/invoices"),
        ]:
            path = BASE_DIR / src
            if path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        zf.write(f, str(basedir / dst / f.relative_to(path)))
            elif path.is_file():
                zf.write(path, str(basedir / dst))
    print(f"  Portable ZIP: {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("  Unzip on Windows and run run.bat")


def main():
    parser = argparse.ArgumentParser(
        description="Build Windows installer / bundle for rental-mgmt"
    )
    parser.add_argument("--innosetup", action="store_true",
                        help="Build InnoSetup installer only (.exe)")
    parser.add_argument("--wix", action="store_true",
                        help="Build WiX MSI installer only (.msi)")
    parser.add_argument("--zip", action="store_true",
                        help="Build portable ZIP bundle only")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("INFO: Running on non-Windows. Will check for Windows tools via WSL paths.")

    build_frontend()

    any_selected = args.innosetup or args.wix or args.zip
    want_innosetup = args.innosetup or (not any_selected and _find_windows_exe("iscc"))
    want_zip = args.zip or (not any_selected and not (want_innosetup or args.wix))

    if want_innosetup:
        build_innosetup()
    if args.wix:
        print("  SKIP: WiX no compatible con este flujo (sin PyInstaller).")
    if want_zip:
        build_zip()

    print()
    print("=" * 50)
    print("  Build complete!")
    print("=" * 50)
    if want_innosetup:
        for p in (BASE_DIR / "dist").glob("rental-mgmt-setup-*.exe"):
            print(f"  InnoSetup: {p}")
    if want_zip:
        zipf = BASE_DIR / "dist" / "rental-mgmt-portable.zip"
        if zipf.exists():
            print(f"  ZIP:       {zipf}")


if __name__ == "__main__":
    main()
