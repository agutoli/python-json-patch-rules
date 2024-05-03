import pytest
from json_patch_rules import patch_rules

@pytest.fixture
def sample_data():
    return {
        "root_key_1": {
            "dog_key_1": False,
            "dog_key_2": 123,
            "dog_key_3": "bark"
        },
        "root_key_2": {
            "cat_key_1": False,
            "cat_key_2": [
                "cat_array_1",
                "cat_array_2"
            ]
        },
        "root_key_3": ["root_array_1", "root_array_2"]
    }

def test_denied_paths(sample_data):
    patch = patch_rules([
        "root_key_1.dog_key_1"  # Only this path is allowed
    ])

    result = patch.apply(sample_data, {
        "root_key_1": {
            "dog_key_2": "it will be denied"
        }
    })

    assert result.denied_paths == ["root_key_1.dog_key_2"], "Should deny updates to non-whitelisted paths"


def test_wildcard_rules_succeed_paths(sample_data):
    patch = patch_rules(["root_key_1.*"])  # All sub-keys of root_key_1 are allowed

    result = patch.apply(sample_data, {
        "root_key_1": {
            "dog_key_1": True,
            "dog_key_2": 456  # Changed from 1 to 456 for clarity
        }
    })

    assert result.successed_paths == ['root_key_1.dog_key_1', 'root_key_1.dog_key_2'], \
        "Should allow updates to all fields under root_key_1 due to wildcard rule"


def test_enum_keys_rules_succeed_paths(sample_data):
    patch = patch_rules(["root_key_1.{dog_key_1,dog_key_3}"])  # Allow specific keys under root_key_1

    result = patch.apply(sample_data, {
        "root_key_1": {
            "dog_key_1": True,
            "dog_key_2": "this will be denied",  # Expect this to be denied
            "dog_key_3": "new bark"
        }
    })

    assert result.successed_paths == ['root_key_1.dog_key_1', 'root_key_1.dog_key_3'], \
        "Should only allow updates to dog_key_1 and dog_key_3"
    assert "root_key_1.dog_key_2" in result.denied_paths, "dog_key_2 update should be denied"

def test_allow_replace_array_with_wildcard(sample_data):
    patch = patch_rules(["root_key_3[*]"])  # Allow all items in the array at root_key_3

    result = patch.apply(sample_data, {
        "root_key_3": ["new_array_1", "new_array_2", "new_array_3"]
    })

    assert result.successed_paths == ['root_key_3[0]', 'root_key_3[1]', 'root_key_3[2]'], \
        "Should allow updates to all elements in the root_key_3 array"

def test_allow_replace_array_unique_values(sample_data):
    patch = patch_rules(["root_key_3[:unique:]"])

    result = patch.apply(sample_data, {
        "root_key_3": ["a", "b", "b", "b", 1, 2, 2]
    })

    assert result.patched_data["root_key_3"] == ['a', 'b', 1, 2], \
        "Should remove duplicated values"


def test_allow_replace_array(sample_data):
    patch = patch_rules(["root_key_3[:replace:]"])

    result = patch.apply(sample_data, {
        "root_key_3": ["replaced_value"]
    })

    assert result.patched_data["root_key_3"] == ["replaced_value"], \
        "Should replace the whole array with anything"
