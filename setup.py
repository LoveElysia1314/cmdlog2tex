from setuptools import setup, find_packages
import os

# Read README (optional)
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cmdlog2tex",
    version="0.9.0",
    description="Convert terminal logs and command streams to LaTeX with ANSI color support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="cmdlog2tex contributors",
    license="MIT",
    url="https://github.com/LoveElysia1314/cmdlog2tex",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "lxml",  # optional, if you plan to add html2tex later
        "cssutils",  # optional
        "cssselect",  # optional
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "cmd2log = cmdlog2tex.main:main",
            "log2tex = cmdlog2tex.main:main",
            "cmd2tex = cmdlog2tex.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",  # ← 关键：声明跨平台
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Markup :: LaTeX",
        "Topic :: Utilities",
    ],
    keywords="latex terminal ansi log conversion",
)
