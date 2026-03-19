from setuptools import setup, find_packages

setup(
    name="booklore-cli",
    version="0.1.0",
    description="CLI tool for managing BookLore - a self-hosted book collection manager",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
        "prompt-toolkit>=3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-mock>=3.0",
            "responses>=0.23",
        ],
    },
    entry_points={
        "console_scripts": [
            "booklore=cli_anything.booklore.main:cli",
        ],
    },
    package_data={
        "cli_anything.booklore": ["skills/*.md"],
    },
)
