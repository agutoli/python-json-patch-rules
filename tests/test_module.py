# test_json_patch_rules.py

import pytest
from json_patch_rules import JsonPatchRules, patch_rules

def test_replace_at_root_level():
    rules = ["*|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result["user"]["name"] == "new", "Should replace the entire user object"

def test_deny_replace_at_root_level():
    rules = ["!*|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"name": "new"}}
    result = patch.apply(old_data, new_data)
    assert result["user"]["name"] == "old", "Should not replace the entire user object due to deny rule"

def test_replace_any_object_keys_values():
    rules = ["{*}|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "age": 30}}
    new_data = {"user": {"name": "new", "age": 30}}
    result = patch.apply(old_data, new_data)
    assert result["user"]["name"] == "new", "Should replace name key in any object"

def test_replace_any_list_index_values():
    rules = ["[*]|replace"]
    patch = patch_rules(rules)
    old_data = [{"user": {"name": "old", "age": 30}}]
    new_data = [{"user": {"name": "new", "age": 30}}]
    result = patch.apply(old_data, new_data)
    assert result[0]["user"]["name"] == "new", "Should replace name key in any object"

def test_deny_replace_any_object_keys_values():
    rules = ["!{*}|replace"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old", "age": 30}}
    new_data = {"user": {"name": "new", "age": 30}}
    result = patch.apply(old_data, new_data)
    assert result["user"]["name"] == "old", "Should deny replacing name key in any object"

def test_implicit_set_allowed():
    rules = ["user"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"age": 30}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "age" in result["user"], "Should allow setting new attributes"

def test_implicit_set_denied():
    rules = ["!user"]
    patch = patch_rules(rules)
    old_data = {"user": {"name": "old"}}
    new_data = {"user": {"age": 30}}  # Attempt to add a new key
    result = patch.apply(old_data, new_data)
    assert "age" not in result["user"], "Should deny setting new attributes"

# Continue writing tests for each rule spec
