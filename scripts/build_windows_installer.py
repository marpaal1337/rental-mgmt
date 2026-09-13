"""Build the Windows package for rental-mgmt.

Usage:
    python scripts/build_windows_installer.py             # PyInstaller + InnoSetup .exe
    python scripts/build_windows_installer.py --innosetup # InnoSetup .exe only
    python scripts/build_windows_installer.py --zip       # Portable .zip only
    python scripts/build_windows_installer.py --skip-frontend

Requirements (Windows):
    InnoSetup: https://jrsoftware.org/isdl.php (add iscc to PATH)
    PyInstaller + Pillow: pip install -e ".[dev]"

Pipeline: icon → frontend build → PyInstaller onedir (dist/rental-mgmt/) →
InnoSetup packages the onedir output and/or ZIP bundles it.
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ONEDIR = BASE_DIR / "dist" / "rental-mgmt"


def _find_windows_exe(name: str) -> str | None:
    """Find a Windows executable, checking WSL paths too."""
    exe = shutil.which(name)
    if exe:
        return exe
    name_lower = name.lower().removesuffix(".exe")
    search_dirs = []
    for p in [Path("/mnt/c/Program Files (x86)"), Path("/mnt/c/Program Files")]:
        if p.exists():
            search_dirs.append(p)
    for env_var in ["ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"]:
        val = os.environ.get(env_var)
        if val:
            p = Path(val)
            if p.exists():
                search_dirs.append(p)
    for root in search_dirs:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() == ".exe" and p.stem.lower() == name_lower:
                return str(p)
    return None


def build_frontend():
    print("→ Building frontend...")
    result = subprocess.run(
        "npm run build",
        cwd=str(BASE_DIR / "frontend"),
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
        print("ERROR building frontend:", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("  Frontend built successfully")


def build_icon():
    print("→ Generating application icon...")
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts" / "generate_icon.py")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR generating icon:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())


def build_pyinstaller():
    print("→ Building executables with PyInstaller...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(BASE_DIR / "rental-mgmt.spec"),
            "--clean",
            "--noconfirm",
        ],
        cwd=str(BASE_DIR),
    )
    if result.returncode != 0:
        print("ERROR building PyInstaller bundle", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"  Executable bundle: {ONEDIR}")


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

    setups = sorted((BASE_DIR / "dist").glob("rental-mgmt-setup-*.exe"))
    if setups:
        print(f"  InnoSetup installer: {setups[-1]}")
    else:
        print("  InnoSetup installer created in dist/")


def build_zip():
    print("→ Building portable ZIP bundle...")
    dist_dir = BASE_DIR / "dist"
    zip_path = dist_dir / "rental-mgmt-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in ONEDIR.rglob("*"):
            if f.is_file():
                zf.write(f, str(Path("rental-mgmt") / f.relative_to(ONEDIR)))
    print(f"  Portable ZIP: {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Build the Windows package for rental-mgmt"
    )
    parser.add_argument("--innosetup", action="store_true",
                        help="Build InnoSetup installer only (.exe)")
    parser.add_argument("--zip", action="store_true",
                        help="Build portable ZIP bundle only")
    parser.add_argument("--skip-frontend", action="store_true",
                        help="Skip frontend build (use existing frontend/dist/)")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("INFO: Running on non-Windows. The bundled executable will target this OS.")

    build_icon()
    if args.skip_frontend:
        print("  Skipping frontend build (--skip-frontend)")
    else:
        build_frontend()

    build_pyinstaller()

    any_selected = args.innosetup or args.zip
    want_innosetup = args.innosetup or (not any_selected and _find_windows_exe("iscc"))
    want_zip = args.zip or not any_selected

    if want_innosetup:
        build_innosetup()
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
