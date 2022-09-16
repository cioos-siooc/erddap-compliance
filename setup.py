import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "erddap_compliance",
    packages=["erddap_compliance"],
    version = "0.0.1",
    description = ("Run ioos-compliance on all datasets of an ERDDAP server"),
    license = "AGPLv3",
    install_requires=read("requirements.txt").splitlines()
)