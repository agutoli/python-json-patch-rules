# tests/test_module.py
from json_patch_rules import patch_rules

patch = patch_rules([
    "{a,b}.test"
])

data = {
    "b": "keep",
    "a": {"test": "bbbb"}
}

new_data = {
    "a": {"test": "overwrite"},
    "c": {"test": "bbbb"}
}

result = patch.apply(data, new_data)

if result.is_patched:
    print(result.patched_data)
else:
    print(result.denied_paths)
