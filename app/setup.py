"""
Setup configuration for Pentagon Photonic Crystal Simulator
Allows installation via: pip install -e .
Or build executable via: python setup.py build_exe
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README_APP.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text()

setup(
    name="pentagon-photonic-simulator",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Interactive GUI for Pentagon Photonic Crystal Structure Analysis with MEEP Simulations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pentagon-photonic-simulator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.20.0",
        "matplotlib>=3.3.0",
        "scipy>=1.7.0",
        "Pillow>=8.0.0",
    ],
    extras_require={
        "meep": ["pymeep>=1.25.0"],
        "gpu": ["cupy-cuda11x>=10.0.0"],  # Adjust CUDA version as needed
        "all": ["pymeep>=1.25.0", "cupy-cuda11x>=10.0.0"],
    },
    entry_points={
        "console_scripts": [
            "pentagon-simulator=app:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
