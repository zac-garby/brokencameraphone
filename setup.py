from setuptools import setup, find_packages

setup(
    name="brokencameraphone",
    version="1.0",
    description="A game.",
    author="Zac Garby",
    author_email="me@zacgarby.co.uk",
    packages=find_packages(),
    install_requires=["Flask", "bcrypt"]
)