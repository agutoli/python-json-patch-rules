from setuptools import setup, find_packages

setup(
    name="jsonpatchrules",
    version="0.1.0",
    author="Your Name",
    author_email="bruno.agutoli@gmail.com",
    description="A short description of your package",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jsonpatchrules",
    package_dir={'': 'jsonpatchrules'},
    packages=find_packages(where='src'),
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.1"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Include package data files from MANIFEST.in, if you have one:
    include_package_data=True,
)
