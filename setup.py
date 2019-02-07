import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="qumquat-prall",
    version="0.0.1",
    author="Patrick Rall",
    author_email="patrickjrall@gmail.com",
    description="An experimental high-level quantum programming language.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/patrickrall/qumquat",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
