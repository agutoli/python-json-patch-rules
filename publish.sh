#/bin/bash

rm -rf dist/ build/
rm -rf python_json_patch_rules.egg-info*

python -m pip install --upgrade setuptools wheel
python setup.py sdist bdist_wheel
python -m pip install --upgrade twine
twine upload dist/*
