from setuptools import setup

setup(
    name="brokencameraphone",
    version="1.0",
    description="A game.",
    author="Zac Garby",
    author_email="me@zacgarby.co.uk",
    packages=["brokencameraphone"],
    install_requires=["Flask", "bcrypt"]
)