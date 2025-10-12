#!/usr/bin/env python3
"""
cmdlog2tex - Command Log to LaTeX Converter
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class PostInstallCommand(install):
    """Post-installation check for system dependencies."""

    def run(self):
        install.run(self)

        print("\n" + "=" * 60)
        print("cmdlog2tex installation completed!")
        print("=" * 60)

        # Check for system dependencies
        missing = []

        try:
            subprocess.run(
                ["aha", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("aha")

        try:
            subprocess.run(
                ["script", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("script (util-linux)")

        if missing:
            print("\n⚠️  WARNING: Missing system dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            print("\nTo install on Ubuntu/Debian:")
            print("  sudo apt install aha util-linux")
            print("\nNote: 'cmd2tex' requires 'script', 'log2tex' requires 'aha'")
        else:
            print("\n✓ All system dependencies found!")

        print("\nInstalled commands:")
        print("  cmd2tex - Execute command streams and convert to LaTeX")
        print("  log2tex - Convert logs to LaTeX")
        print("\nTry: cmd2tex --help")
        print("     log2tex --help")
        print("=" * 60 + "\n")


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="cmdlog2tex",
    version="0.8.0",
    author="cmdlog2tex contributors",
    description="Execute command streams and convert terminal logs to LaTeX",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LoveElysia1314/cmdlog2tex",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Markup :: LaTeX",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "cmd2tex=cmdlog2tex.cmd2tex:main",
            "log2tex=cmdlog2tex.log2tex:main",
        ],
    },
    cmdclass={
        "install": PostInstallCommand,
    },
)
