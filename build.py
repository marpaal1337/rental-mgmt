"""Build script: compiles frontend and packages everything into a portable folder.

Usage:
    python build.py   # Build for current platform (onedir — folder with EXE + deps)

The spec always produces a COLLECT (onedir folder) so the installer can
package all files. Output: dist/rental-mgmt/
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


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


def build_executable():
    print("→ Building executable...")
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
        print("ERROR building executable", file=sys.stderr)
        sys.exit(result.returncode)

    out = BASE_DIR / "dist" / "rental-mgmt"
    print(f"  Portable folder created in {out}")


def main():
    build_frontend()
    build_executable()

    print()
    print("=" * 50)
    print("  Build complete!")
    print("=" * 50)
    out = BASE_DIR / "dist" / "rental-mgmt"
    exe_name = "rental-mgmt.exe" if os.name == "nt" else "rental-mgmt"
    print(f"  Portable folder: {out}")
    print(f"  Run: {out / exe_name}")
    print()
    print("  To create a Windows installer, run:")
    print("    python scripts/build_windows_installer.py --skip-pyinstaller")


if __name__ == "__main__":
    main()
