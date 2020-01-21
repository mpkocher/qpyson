import os
from setuptools import setup

version = __import__("qpyson").__version__


def _get_local_file(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def _read(file_name):
    with open(_get_local_file(file_name)) as f:
        return f.read()


setup(
    name="qpyson",
    version=version,
    description="JQ-ish tool to query/munge JSON files using Python",
    long_description=_read("README.md"),
    long_description_content_type="text/markdown",
    url="http://github.com/mpkocher/qpyson",
    author="M. Kocher",
    author_email="michael.kocher@me.com",
    license="MIT",
    packages=["qpyson"],
    entry_points={"console_scripts": ["qpyson=qpyson.cli:run_main"]},
    tests_require=["nose"],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["tabulate"],
)
