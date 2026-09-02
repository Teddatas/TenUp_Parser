"""
Setup pour tedata-tennis
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tedata-tennis",
    version="0.1.0",
    author="Teddy",
    author_email="your-email@example.com",
    description="Parser de tournois de tennis depuis PDF vers CSV",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Teddatas/tedata-tennis",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pdfplumber>=0.9.0",
        "pandas>=1.5.0",
        "openpyxl>=3.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "flake8>=5.0",
            "black>=22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tedata-tennis=main:main",
        ],
    },
)
