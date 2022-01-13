import pathlib
from setuptools import setup
import codecs

version = ""
with open('VERSION') as fp:
    version = fp.read()


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


with codecs.open('README.md', mode='r', encoding='utf-8') as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="obasparql",
    version=version,
    description="OBA Sparql Manager",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/KnowledgeCaptureAndDiscovery/oba_sparql",
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
    install_requires=[
        "validators==0.15.0",
        "pythonql3==0.9.61",
        "pyaml==18.11.0",
        "rdflib==6.1.1",
        "requests>=2.20.0",
        "simplejson==3.16.0",
        "six==1.11.0",
        "urllib3==1.26.5",
        "webencodings==0.5.1",
        "werkzeug>=0.15.3",
        "PyLD==1.0.5",
    ]
)
