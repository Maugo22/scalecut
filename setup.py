from setuptools import setup, find_packages

setup(
    name="scalecut",
    version="0.1.0",
    description="Video production workflow scaffolding for editors and agencies.",
    author="ScaleCut",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "questionary>=2.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": ["pytest>=8.0.0"],
    },
    entry_points={
        "console_scripts": [
            "scalecut=scalecut.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
