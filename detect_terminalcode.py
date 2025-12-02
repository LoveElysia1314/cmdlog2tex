#!/usr/bin/env python3
"""
Detect if the system has installed the terminalcode LaTeX package

Use multiple methods for comprehensive detection, support Windows, Linux, macOS cross-platform
"""

import os
import sys
import platform
import subprocess
from typing import List, Optional


class TerminalcodeDetector:
    """terminalcode package detection tool"""

    @staticmethod
    def detect_via_kpsewhich() -> bool:
        """
        Method 1: Use kpsewhich (most reliable)

        Return: True means package found
        """
        try:
            result = subprocess.run(
                ["kpsewhich", "terminalcode.sty"],
                capture_output=True,
                timeout=2,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                print(f"  ✓ kpsewhich found package: {result.stdout.strip()}")
                return True
            return False
        except FileNotFoundError:
            return False
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    @staticmethod
    def get_texmf_candidates() -> List[str]:
        """Get all possible TEXMF directories"""
        candidates = []
        home = os.path.expanduser("~")
        system = platform.system()

        if system == "Windows":
            bases = [
                "C:\\texlive",
                "C:\\Program Files\\MiKTeX",
                os.path.join(os.environ.get("APPDATA", ""), "MiKTeX"),
                os.path.join(home, "texmf"),
            ]
            for base in bases:
                if os.path.exists(base):
                    candidates.extend(
                        [
                            os.path.join(
                                base, "texmf-dist", "tex", "latex", "terminalcode"
                            ),
                            os.path.join(base, "texmf-dist", "tex", "latex"),
                            os.path.join(base, "tex", "latex"),
                        ]
                    )
        else:  # Linux / macOS
            bases = [
                "/usr/local/texlive",
                "/usr/share/texlive",
                "/opt/texlive",
                os.path.join(home, "texmf"),
                os.path.join(home, ".texmf"),
            ]
            for base in bases:
                if os.path.exists(base):
                    candidates.extend(
                        [
                            os.path.join(
                                base, "texmf-dist", "tex", "latex", "terminalcode"
                            ),
                            os.path.join(base, "texmf-dist", "tex", "latex"),
                            os.path.join(base, "tex", "latex"),
                        ]
                    )

        return candidates

    @staticmethod
    def detect_via_directory_search() -> bool:
        """
        Method 2: Search standard TEXMF directories
        """
        try:
            candidates = TerminalcodeDetector.get_texmf_candidates()

            for directory in candidates:
                sty_path = os.path.join(directory, "terminalcode.sty")
                if os.path.isfile(sty_path):
                    print(f"  ✓ Directory search found package: {sty_path}")
                    return True

                # Also check the directory itself
                if os.path.isdir(directory):
                    try:
                        for filename in os.listdir(directory):
                            if filename == "terminalcode.sty":
                                full_path = os.path.join(directory, filename)
                                print(
                                    f"  ✓ Directory search found package: {full_path}"
                                )
                                return True
                    except PermissionError:
                        continue

            return False
        except Exception:
            return False

    @staticmethod
    def detect_via_tlmgr() -> Optional[bool]:
        """
        Method 3: Use tlmgr query (TeX Live only)

        Return:
            True  - Package found
            False - Package not found
            None  - tlmgr unavailable
        """
        try:
            result = subprocess.run(
                ["tlmgr", "list", "--only-installed"],
                capture_output=True,
                timeout=5,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                if "terminalcode" in result.stdout.lower():
                    print("  ✓ tlmgr query: package installed")
                    return True
                return False
            return None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    @staticmethod
    def detect_comprehensive() -> bool:
        """
        Comprehensive detection (recommended)

        Return: True means system has package installed, False means not installed
        """
        print("=" * 70)
        print("Detecting terminalcode LaTeX package...")
        print("=" * 70)

        system = platform.system()
        print(f"System: {system}")
        print(f"Python: {sys.version.split()[0]}")
        print()

        # Method 1: kpsewhich
        print("[Method 1] Using kpsewhich...")
        if TerminalcodeDetector.detect_via_kpsewhich():
            print()
            print("=" * 70)
            print("✅ Detection result: system has terminalcode package installed")
            print("=" * 70)
            return True
        print("  ✗ kpsewhich not found")

        # Method 2: Directory search
        print("\n[Method 2] Searching standard directories...")
        if TerminalcodeDetector.detect_via_directory_search():
            print()
            print("=" * 70)
            print("✅ Detection result: system has terminalcode package installed")
            print("=" * 70)
            return True
        print("  ✗ Not found in standard directories")

        # Method 3: tlmgr
        print("\n[Method 3] Using tlmgr query...")
        tlmgr_result = TerminalcodeDetector.detect_via_tlmgr()
        if tlmgr_result is True:
            print()
            print("=" * 70)
            print("✅ Detection result: system has terminalcode package installed")
            print("=" * 70)
            return True
        elif tlmgr_result is False:
            print("  ✗ tlmgr query: package not installed")
        else:
            print("  ⚠ tlmgr unavailable")

        # System package not found
        print()
        print("=" * 70)
        print(
            "❌ Detection result: system does not have terminalcode package installed"
        )
        print("=" * 70)
        print()
        print("Installation suggestions:")
        print()

        if platform.system() == "Windows":
            print("  Windows (TeX Live):")
            print(
                "    1. Open PowerShell or cmd (administrator privileges recommended)"
            )
            print("    2. Run commands:")
            print("       tlmgr update --self")
            print("       tlmgr install terminalcode")
            print()
            print("  Windows (MiKTeX):")
            print("    1. Open MiKTeX Package Manager")
            print("    2. Search 'terminalcode'")
            print("    3. Click 'Install'")
        else:
            print("  Linux / macOS:")
            print("    Run command:")
            print("      tlmgr update --self")
            print("      tlmgr install terminalcode")
            print()
            if platform.system() == "Linux":
                print("    Or use system package manager (if available):")
                print("      # Ubuntu/Debian")
                print("      apt install texlive-latex-extra")

        print()
        print("  Alternative when unable to install:")
        print(
            "    • cmdlog2tex will automatically copy the local backup terminalcode.sty"
        )
        print("    • The generated .tex file can still compile normally")

        print()
        return False


if __name__ == "__main__":
    has_package = TerminalcodeDetector.detect_comprehensive()
    sys.exit(0 if has_package else 1)
