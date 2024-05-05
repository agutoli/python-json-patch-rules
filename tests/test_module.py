from json_patch_rules import patch_rules

def test_replace_at_root_level():
    rules = ["*|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "new", "Should replace the entire user object"

def test_deny_replace_at_root_level():
    rules = ["!*|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "old", "Should not replace the entire user object due to deny rule"

def test_replace_any_object_keys_values():
    rules = ["{*}|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "age": 30}}
    new_data = {"user": {"name": "new", "age": 30}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "new", "Should replace name key in any object"

def test_replace_any_list_index_values():
    rules = ["[*]|replace"]
    patch = patch_rules(rules)
    old_data = [{"user": {"name": "old", "age": 30}}]
    new_data = [{"user": {"name": "new", "age": 30}}]
    result = patch.apply(old_data, new_data)
    assert result.data[0]["user"]["name"] == "new", "Should replace name key in any object"

def test_deny_replace_any_object_keys_values():
    rules = ["!{*}|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "age": 30}}
    new_data = {"user": {"name": "new", "age": 30}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "old", "Should deny replacing name key in any object"

def test_implicit_set_denied():
    rules = ["!user"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"age": 30}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "age" not in result.data["user"], "Should deny setting new attributes"

def test_deny_set_non_authorized_keys():
    rules = ["user.contacts"]
    patch = patch_rules(rules)
    old_data = {}
    new_data = {"user": {"other_key": "will be denied"}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert {} == result.data, "Should deny setting new attributes"

def test_replace_root_array():
    rules = ["[*]|replace"]
    patch = patch_rules(rules)
    old_data = ["will_be_replaced"]
    new_data = ["d"]
    result = patch.apply(old_data, new_data)
    assert ["d"] == result.data, "Should replace the old value with the new array"

def test_implicit_set_allowed():
    rules = ["user"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"age": 30}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "old" == result.data["user"]["name"], "Should allow setting new attributes"
    assert 30 == result.data["user"]["age"], "Should allow setting new attributes"

def test_replace_nested_array_attribute():
    rules = ["user.contacts|replace"]
    patch = patch_rules(rules)
    old_data = {
        "user": {
            "contacts": ["a", "b", "c"]
        }
    }
    new_data = {
        "user": {
            "contacts": ["d"]
        }
    }
    result = patch.apply(old_data, new_data)
    assert ["d"] == result.data["user"]["contacts"], "Should replace the old value with the new array"

def test_replace_and_unique_nested_array_attribute():
    rules = [
        "user.array_1|replace|unique"
    ]
    patch = patch_rules(rules)
    old_data = {
        "user": {
            "array_1": ["a", "b"],
            "array_2": ["same value"]
        }
    }
    new_data = {
        "user": {
            "array_1": ["a", "a", "b", "c", "d", "d"],
            "array_2": ["value_will_be_ignored"]
        }
    }
    result = patch.apply(old_data, new_data)
    assert ['a', 'b', 'c', 'd'] == result.data["user"]["array_1"], "Should replace the old value with the new array"
    assert ['same value'] == result.data["user"]["array_2"], "Should replace the old value with the new array"

def test_replace_and_unique_multiple_rules():
    rules = [
        "user.array_1|replace|unique",
        "user.array_2|replace"
    ]
    patch = patch_rules(rules)
    old_data = {
        "user": {
            "array_1": ["a", "b"]
        }
    }
    new_data = {
        "user": {
            "array_1": ["a", "a", "b", "c", "d", "d"],
            "array_2": ["c", "c"]
        }
    }
    result = patch.apply(old_data, new_data)
    assert ['a', 'b', 'c', 'd'] == result.data["user"]["array_1"], "Should replace the old value with the new array"
    assert ["c", "c"] == result.data["user"]["array_2"], "Should replace the old value with the new array"


def test_replace_root_dict():
    rules = ["{*}|replace"]
    patch = patch_rules(rules)
    old_data = {"will_be_replaced": 1}
    new_data = {"b": 2}
    result = patch.apply(old_data, new_data)
    assert {"b": 2} == result.data, "Should replace old value with new dict"

def test_root_implicit_object_set_allowed():
    rules = ["{*}"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"age": 30}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "age" in result.data["user"], "Should allow setting new attributes"
    assert "name" in result.data["user"], "Should allow setting new attributes"

def test_root_implicit_list_set_allowed():
    rules = ["[*]"]
    patch = patch_rules(rules)
    old_data = [{"user": {"name": "old"}}]
    new_data = [{"user": {"age": 30}}]  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "age" in result.data[0]["user"], "Should allow setting new attributes"
    assert "name" in result.data[0]["user"], "Should allow setting new attributes"

def test_set_nested_array_any_index():
    rules = ["user.contacts[*].label"]
    patch = patch_rules(rules)
    old_data = {"user": {"contacts": [{"label": "old value"}]}}
    new_data = {"user": {"contacts": [{"label": "new value"}]}}
    result = patch.apply(old_data, new_data)
    assert "new value" == result.data["user"]["contacts"][0]["label"], "Should allow setting new attributes"

def test_deny_set_nested_array_any_index():
    rules = ["!user.contacts[*].label"]
    patch = patch_rules(rules)
    old_data = {"user": {"contacts": [{"label": "old value"}]}}
    new_data = {"user": {"contacts": [{"label": "new value"}]}}
    result = patch.apply(old_data, new_data)
    assert "old value" == result.data["user"]["contacts"][0]["label"], "Should allow setting new attributes"

def test_no_change_for_nonexistent_paths():
    rules = ["non.existent.path|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "old", "Non-existent paths should not affect data"

def test_malformed_rules():
    rules = ["this|is|not|a|valid|rule"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "old", "Malformed rules should not affect data"
    assert result.denied_paths == ["user.name"]
    assert result.successed_paths == []

def test_mixed_valid_and_invalid_operations():
    rules = ["user.name|replace", "!user.age|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "age": 20}}
    new_data = {"user": {"name": "new", "age": 30}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "new", "Valid operation should succeed"
    assert result.data["user"]["age"] == 20, "Invalid operation should be denied"

def test_empty_data_handling():
    rules = ["*|replace"]
    patch = patch_rules(rules)
    old_data = {}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result.data == {"user": {"name": "new"}}, "Should handle empty old data correctly"

    old_data = {"user": {"name": "old"}}
    new_data = {}
    result = patch.apply(old_data, new_data)
    assert result.data == {}, "Should handle empty new data correctly"

def test_recursive_data_structures():
    rules = ["user|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "self": "reference"}}
    new_data = {"user": {"name": "new", "self": old_data["user"]}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["name"] == "new", "Should replace user correctly"
    assert result.data["user"]["self"]["name"] == "old", "Should handle recursive structures"

def test_implicit_set_index_zero():
    rules = ["[0]"]
    patch = patch_rules(rules)
    old_data = ["old_value", "another_value"]
    new_data = ["new_value", "another_value"]
    result = patch.apply(old_data, new_data)
    assert result.data[0] == "new_value", "Should allow setting new value at index zero"
    assert result.data[1] == "another_value", "Should not modify other indices"

def test_deny_specific_nested_property():
    rules = ["!user.contacts[0].phone"]
    patch = patch_rules(rules)
    old_data = {"user": {"contacts": [{"phone": "old_phone"}]}}
    new_data = {"user": {"contacts": [{"phone": "new_phone"}]}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["contacts"][0]["phone"] == "old_phone", "Should deny setting new phone number"
    assert result.denied_paths == ["user.contacts[0].phone"]
    assert result.successed_paths == []

def test_allow_and_deny_properties_at_any_index():
    rules = ["user.contacts[*].label", "!user.contacts[*].phone"]
    patch = patch_rules(rules)
    old_data = {"user": {"contacts": [{"label": "old_label", "phone": "old_phone"}]}}
    new_data = {"user": {"contacts": [{"label": "new_label", "phone": "new_phone"}]}}
    result = patch.apply(old_data, new_data)
    assert result.data["user"]["contacts"][0]["label"] == "new_label", "Should allow setting new label"
    assert result.data["user"]["contacts"][0]["phone"] == "old_phone", "Should deny setting new phone number"

def test_unique_rule_on_array_of_strings():
    rules = ["[*]|unique"]
    patch = patch_rules(rules)
    old_data = ["a", "b", "a", "c"]
    new_data = ["d", "d", "e", "f", "f"]

    result = patch.apply(old_data, new_data)
    assert result.data == ['a', 'b', 'c', 'd', 'e', 'f'], "Should apply unique rule and remove duplicates"

def test_nested_unique_rule_on_array_of_strings():
    rules = ["nested.items[*]|unique"]
    patch = patch_rules(rules)
    old_data = {"nested": {"items": ["a", "b", "a", "c"]}}
    new_data = {"nested": {"items": ["d", "d", "e", "f", "f"]}}

    result = patch.apply(old_data, new_data)
    assert result.data["nested"]["items"] == ['a', 'b', 'c', 'd', 'e', 'f'], "Should apply unique rule and remove duplicates"
    assert result.denied_paths == []
    assert result.successed_paths == ['nested.items[0]', 'nested.items[1]', 'nested.items[2]', 'nested.items[3]', 'nested.items[4]']