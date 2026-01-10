#!/usr/bin/env python3
"""Setup script for Quant Market Analysis Engine."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="quant-engine",
    version="1.0.0",
    author="Trading Indicator Project",
    description="Quantitative market analysis engine with Hurst, Kalman, Z-Score, and Volume analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tempest-Zero/trading-indicator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "data": [
            "yfinance>=0.1.70",
            "ccxt>=2.0.0",
        ],
        "viz": [
            "plotly>=5.0.0",
            "matplotlib>=3.4.0",
        ],
        "kalman": [
            "pykalman>=0.9.5",
        ],
        "full": [
            "yfinance>=0.1.70",
            "ccxt>=2.0.0",
            "plotly>=5.0.0",
            "matplotlib>=3.4.0",
            "pykalman>=0.9.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-engine=quant_engine.main:main",
        ],
    },
)
