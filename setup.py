from setuptools import setup, find_packages

setup(
    name="aegis-middleware",
    version="0.1.0",
    description="Redis-backed sliding window rate limiting middleware for FastAPI",
    author="Arihanth Sharma",
    packages=find_packages(),
    install_requires=[
        "redis>=4.2.0",
    ],
    python_requires=">=3.9",
)
