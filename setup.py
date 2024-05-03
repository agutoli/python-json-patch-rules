from setuptools import setup, find_packages

setup(
    name="python-json-patch-rules",
    version="0.2.0",
    author="Bruno Agutoli",
    author_email="bruno.agutoli@gmail.com",
    description="A library to apply JSON patches with rule-based access control.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/agutoli/python-json-patch-rules",
    # Correct the package_dir to point to 'json_patch_rules' since your actual package code is there
    package_dir={'': '.'},
    # Since your package is inside the 'json_patch_rules', the 'where' should be corrected from 'src' to 'json_patch_rules'
    packages=find_packages(where='json_patch_rules'),
    python_requires=">=3.6",
    install_requires=[
        # It seems like you might not actually need 'requests'. Verify if you really need this dependency.
        # If pydash is used in your code, make sure it's included in install_requires
        "pydash"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Ensure you include package data correctly, especially if using MANIFEST.in
    include_package_data=True,
)
