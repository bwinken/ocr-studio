"""Build OCR Studio .exe using PyInstaller."""

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
BUILD_DIR = PROJECT_DIR / "build"


def build_exe():
    """Run PyInstaller with our spec file."""
    print("Building OCR Studio .exe...")
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            str(BUILD_DIR / "ocr-studio.spec"),
            "--distpath", str(BUILD_DIR / "dist"),
            "--workpath", str(BUILD_DIR / "work"),
        ],
        check=True,
        cwd=str(PROJECT_DIR),
    )
    print(f"Build complete! Output: {BUILD_DIR / 'dist' / 'OCRStudio'}")


def build_installer():
    """Run Inno Setup compiler (must be installed)."""
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc = None
    for p in iscc_paths:
        if Path(p).exists():
            iscc = p
            break

    if not iscc:
        print("Inno Setup not found. Install from https://jrsoftware.org/isdownload.php")
        print("Then re-run with --installer flag.")
        return

    print("Building installer...")
    subprocess.run(
        [iscc, str(BUILD_DIR / "inno-setup.iss")],
        check=True,
        cwd=str(BUILD_DIR),
    )
    print(f"Installer output: {BUILD_DIR / 'output'}")


if __name__ == "__main__":
    build_exe()
    if "--installer" in sys.argv:
        build_installer()
