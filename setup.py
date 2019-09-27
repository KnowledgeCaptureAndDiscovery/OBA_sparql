import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="obasparql",
    version="1.0.0",
    description="OBA Sparql Manager",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/KnowledgeCaptureAndDiscovery/oba_sparql-manager",
    author="Maximiliano Osorio",
    author_email="mosorio@isi.edu",
    license="Apache-2",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Science/Research",
        "Operating System :: Unix",
    ],
    packages=["obasparql"],
    include_package_data=True,
    install_requires=["requests", "urllib3"],
)
