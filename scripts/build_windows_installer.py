"""Build a Windows installer / bundle for rental-mgmt.

Usage:
    python scripts/build_windows_installer.py                   # Build all available
    python scripts/build_windows_installer.py --innosetup       # InnoSetup .exe only
    python scripts/build_windows_installer.py --wix             # WiX .msi only
    python scripts/build_windows_installer.py --zip             # Portable .zip only
    python scripts/build_windows_installer.py --skip-pyinstaller  # Skip PyInstaller

Requirements (Windows):
    pip install pyinstaller
    InnoSetup: https://jrsoftware.org/isdl.php (add iscc to PATH)
    WiX: https://wixtoolset.org (add candle, light, heat to PATH)

On WSL with InnoSetup installed on Windows:
    python scripts/build_windows_installer.py --innosetup       # finds iscc.exe via /mnt/c/
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
    # On WSL, check Windows PATH via /mnt/c/
    name_exe = name if name.endswith(".exe") else f"{name}.exe"
    for root in [Path("/mnt/c/Program Files (x86)"), Path("/mnt/c/Program Files")]:
        for p in root.rglob(name_exe):
            return str(p)
    return None


def build_frontend():
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


def build_pyinstaller():
    print("→ Building PyInstaller (onedir mode)...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller", "-q"],
        capture_output=True,
    )
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "rental-mgmt.spec", "--clean", "--noconfirm",
    ]
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print("ERROR building PyInstaller executable", file=sys.stderr)
        sys.exit(result.returncode)
    print("  PyInstaller done → dist/rental-mgmt/")


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


def build_wix():
    print("→ Building WiX MSI installer...")
    for tool in ["candle", "light", "heat"]:
        if not _find_windows_exe(tool):
            print(f"  SKIP: {tool} (WiX Toolset) not found.", file=sys.stderr)
            print("  Install from: https://wixtoolset.org", file=sys.stderr)
            return

    wix_dir = BASE_DIR / "build" / "wix"
    dist_dir = BASE_DIR / "dist"
    pyinst_dir = dist_dir / "rental-mgmt"

    if not pyinst_dir.exists():
        print("ERROR: PyInstaller output not found.", file=sys.stderr)
        sys.exit(1)

    print("  Harvesting files with heat.exe...")
    heat = _find_windows_exe("heat")
    subprocess.run([
        heat, "dir", str(pyinst_dir),
        "-gg", "-srd", "-sreg",
        "-cg", "RentalMgmtFiles",
        "-dr", "INSTALLDIR",
        "-out", str(wix_dir / "Components.wxs"),
    ], check=True, capture_output=True)
    print("  Components.wxs generated")

    print("  Compiling with candle.exe...")
    candle = _find_windows_exe("candle")
    subprocess.run([
        candle,
        str(wix_dir / "rental-mgmt.wxs"),
        str(wix_dir / "Components.wxs"),
    ], check=True, capture_output=True)

    print("  Linking with light.exe...")
    light = _find_windows_exe("light")
    msi_output = str(dist_dir / "rental-mgmt-0.1.0.msi")
    subprocess.run([
        light,
        str(wix_dir / "rental-mgmt.wixobj"),
        str(wix_dir / "Components.wixobj"),
        "-out", msi_output,
    ], check=True, capture_output=True)

    print(f"  WiX MSI installer: {msi_output}")

    for f in wix_dir.glob("*.wixobj"):
        f.unlink()
    print("  Cleaned up intermediate files")


def build_zip():
    print("→ Building portable ZIP bundle...")
    dist_dir = BASE_DIR / "dist"
    pyinst_dir = dist_dir / "rental-mgmt"

    if not pyinst_dir.exists():
        print("ERROR: PyInstaller output not found.", file=sys.stderr)
        sys.exit(1)

    zip_path = dist_dir / "rental-mgmt-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in pyinst_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(pyinst_dir.parent))

    print(f"  Portable ZIP: {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("  Unzip on Windows and run rental-mgmt.exe")


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
    parser.add_argument("--skip-pyinstaller", action="store_true",
                        help="Skip PyInstaller step (use existing dist/rental-mgmt/)")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("INFO: Running on non-Windows. Will check for Windows tools via WSL paths.")

    if not args.skip_pyinstaller:
        build_frontend()
        build_pyinstaller()

    pyinst_dir = BASE_DIR / "dist" / "rental-mgmt"
    if not pyinst_dir.exists():
        print("ERROR: dist/rental-mgmt/ not found. Run without --skip-pyinstaller.",
              file=sys.stderr)
        sys.exit(1)

    # Determine what to build
    any_selected = args.innosetup or args.wix or args.zip
    want_innosetup = args.innosetup or (not any_selected and _find_windows_exe("iscc"))
    want_wix = args.wix or (not any_selected and _find_windows_exe("candle"))
    want_zip = args.zip or (not any_selected and not (want_innosetup or want_wix))

    if want_innosetup:
        build_innosetup()
    if want_wix:
        build_wix()
    if want_zip:
        build_zip()

    print()
    print("=" * 50)
    print("  Build complete!")
    print("=" * 50)
    if want_innosetup:
        for p in (BASE_DIR / "dist").glob("rental-mgmt-setup-*.exe"):
            print(f"  InnoSetup: {p}")
    if want_wix:
        msi = BASE_DIR / "dist" / "rental-mgmt-0.1.0.msi"
        if msi.exists():
            print(f"  WiX MSI:   {msi}")
    if want_zip:
        zipf = BASE_DIR / "dist" / "rental-mgmt-portable.zip"
        if zipf.exists():
            print(f"  ZIP:       {zipf}")


if __name__ == "__main__":
    main()
