from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="toronto_report_parser",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    author="Bill Shi",
    description="A parser for IOL biometry reports using PyMuPDF.",
    python_requires=">=3.9",
)
