from setuptools import setup, find_packages

setup(
    name="reply_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "aiohttp",
        "pydantic"
    ],
)
