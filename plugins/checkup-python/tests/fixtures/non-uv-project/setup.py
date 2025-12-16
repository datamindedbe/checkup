from setuptools import find_packages, setup

setup(
    name="test-non-uv-project",
    version="0.1.0",
    description="A minimal non-uv test project",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
    ],
)
