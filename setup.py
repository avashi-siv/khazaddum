"""Set this ting up cmon"""
import os

from setuptools import find_packages
from setuptools import setup

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ABOUT = {}
with open(os.path.join(BASE_DIR, "khazaddum", "__about__.py")) as f:
    exec(f.read(), ABOUT)  # pylint: disable=exec-used

setup(
    name=ABOUT["__title__"],
    version=ABOUT["__version__"],
    description=ABOUT["__summary__"],
    url="https://github.com/avashi-siv/khazaddum",
    packages=find_packages(),
    install_requires=["plumbum>=1.6.7, <2.0"],
)
