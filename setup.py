#!/usr/bin/env python3
"""Setup script for Pass Keyboard Control application."""

import os

from setuptools import find_packages, setup


# Read README for long description
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


setup(
    name="pass-keyboard-control",
    version="1.0.0",
    description="AI-generated keyboard-driven GUI for Unix password manager (pass) with total keyboard control",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="mr-scrpt",
    author_email="mr.scrpt@gmail.com",
    url="https://github.com/mr-scrpt/pass-keyboard-control",
    license="MIT",
    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    # Dependencies
    install_requires=[
        "PySide6>=6.5.0",
        "qt-material>=2.14",
        "QtAwesome>=1.2.0",
    ],
    # Python version requirement
    python_requires=">=3.8",
    # Entry points - создает команду 'pass-kb' в системе
    entry_points={
        "console_scripts": [
            "pass-kb=pass_client:main",
        ],
        "gui_scripts": [
            "pass-kb-gui=pass_client:main",
        ],
    },
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Security",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
    ],
    # Keywords
    keywords="password manager gui pass gpg security",
    # Additional files to include
    package_data={
        "": ["*.json", "*.txt", "*.md"],
    },
    # Data files - desktop entry and icon
    data_files=[
        ("share/applications", ["pass-kb.desktop"]),
        # Если есть иконка, раскомментировать:
        # ('share/icons/hicolor/256x256/apps', ['icons/pass-kb.png']),
    ],
)
