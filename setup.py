from setuptools import setup
import sys

if sys.platform != "win32":
    sys.exit("This package is only supported on Windows platforms")

setup()
