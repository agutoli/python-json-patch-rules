import re
import json
import pydash
from typing import Any, Optional, Pattern
from dataclasses import dataclass
from json_patch_rules.__symbols__ import EMPTY_ARRAY_SYMBOL


@dataclass
class RuleItem:
    rule_pattern: str
    replace: bool = False
    unique: bool = False
    replace_path: Optional[str] = None
    pattern: Optional[str] = None
    compile: Optional[Pattern[str]] = None

@dataclass
class PatchResult:
    denied_paths: list[str]
    successed_paths: list[str]
    is_patched: bool
    patched_data: Any
    errors: list[str]


@dataclass
class PatchingStore:
    old_data: Any = None
    new_data: Any = None


class JsonPatchRules:
    ANY_INDEX_WILDCARD     = "0__ANY_INDEX_WILDCARD__0"
    UNIQUE_ITEMS_LIST  = "0__UNIQUE_ITEMS_LIST__0"
    REPLACE_ITEMS_LIST = "0__REPLACE_ITEMS_LIST__0"
    ANY_KEY_WILDCARD   = "0__ANY_KEY_WILDCARD__0"
    ANY_SEG_WILDCARD   = "0__ANY_SEG_WILDCARD__0"

    def __init__(self, rules) -> None:
        self.rules = rules

    def get_paths(self, obj, current_path=""):
        """ Recursively find all paths in a nested JSON object and format them in dot and bracket notation. """
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{current_path}.{k}" if current_path else k
                yield from self.get_paths(v, new_path)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_path = f"{current_path}[{i}]"
                yield from self.get_paths(v, new_path)
        else:
            yield current_path

    def parse_rule(self, rule):
        rule_item = RuleItem(rule_pattern=rule)

        """Convert a permission rule into a regex pattern for matching paths."""
        # Temporary placeholders for complex wildcards to avoid premature escaping
        placeholder_dict = {
            '[:unique:]': self.UNIQUE_ITEMS_LIST,
            '[:replace:]': self.REPLACE_ITEMS_LIST,
            '[*]': self.ANY_INDEX_WILDCARD,
            '{*}': self.ANY_KEY_WILDCARD,
            '*': self.ANY_SEG_WILDCARD,
        }

        for key, value in placeholder_dict.items():
            rule = rule.replace(key, value)

        # Escape the rule to safely turn into regex, then restore placeholders to regex patterns
        rule = re.escape(rule)
        rule = rule.replace(re.escape(self.ANY_INDEX_WILDCARD), r'\[\d+\]')
        rule = rule.replace(re.escape(self.ANY_KEY_WILDCARD), r'[^.]+')
        rule = rule.replace(re.escape(self.ANY_SEG_WILDCARD), r'.+')

        # Replace {key1,key2,...} with regex alternation group
        def replace_options(match):
            options = match.group(1)
            options = '|'.join(re.escape(option.strip()) for option in options.split(','))
            return f"(?:{options})"

        rule = re.sub(r'\\{([^\\}]+)\\}', replace_options, rule)

        # Check if using :unique: and remove all rules after that
        # given we can replace the whole array doing a regular variable assign
        # instead of using pydash.set_()
        unique_items_parts = rule.split(self.UNIQUE_ITEMS_LIST)
        if len(unique_items_parts) > 1:
            rule = unique_items_parts[0] # ignore all properties after [:unique:]
            rule_item.replace = True
            rule_item.unique = True
            rule_item.replace_path = unique_items_parts[0]

        # Allow replace the whole array
        replace_items_parts = rule.split(self.REPLACE_ITEMS_LIST)
        if len(replace_items_parts) > 1:
            rule = rule.replace(re.escape(self.REPLACE_ITEMS_LIST), r'.*')
            rule_item.replace = True
            rule_item.unique = False
            rule_item.replace_path = replace_items_parts[0]
        
        rule_item.compile = re.compile('^' + rule + '$')
        return rule_item

    def replace_with_value(self, data_to_patch, path, values) -> None:
            pydash.set_(data_to_patch, path, values)

    def patch_value(self, data_to_patch, path, values) -> None:
        if not values:
            pydash.unset(data_to_patch, path)
        else:
            pydash.set_(data_to_patch, path, values)

    def verify_permission(self, data_paths, permission_rules):
        """Check if the provided data paths are allowed by the permission rules."""
        rule_items = [self.parse_rule(rule) for rule in permission_rules]
        results = {}
        for path in data_paths:
            for rule_item in rule_items:
                if rule_item.replace and rule_item.replace_path:
                    results[rule_item.replace_path] = [True, rule_item]
                elif rule_item.compile:
                    if rule_item.replace:
                        results[path] = [True, rule_item]
                    else:
                        results[path] = [rule_item.compile.match(path), rule_item]
                else:
                    results[path] = [False, None]
        return results

    def item_checker(self, path, allowed, store, successed, denied_paths, errors):
        if not allowed[0]:
            denied_paths.append(path)
            return successed, denied_paths, errors
        
        if isinstance(store.new_data, list):
            # print(path, EMPTY_ARRAY_SYMBOL, store.new_data)
            # and store.new_data[0] == EMPTY_ARRAY_SYMBOL
            self.patch_value(store.old_data, path, None)
            successed.append(path)
            return successed, denied_paths, errors

        if allowed[1].replace and not allowed[1].unique:
            self.replace_with_value(store.old_data, path, pydash.get(store.new_data, path))
            successed.append(path)
            return successed, denied_paths, errors

        if not allowed[1].unique:
            self.patch_value(store.old_data, path, pydash.get(store.new_data, path))
            successed.append(path)
            return successed, denied_paths, errors

        items_values = pydash.get(store.new_data, path)
        if isinstance(items_values, list):
            try:
                # It can not have boolean
                bools_in_list = [x for x in items_values if isinstance(x, bool)]
                if len(bools_in_list) > 0:
                    error_message = (
                        f"Failed to make unique: boolean found in list at '{path}'. "
                        f"Boleans cannot be used with the [:unique:] modifier because they are unhashable. "
                        f"Encountered error while processing rule: {allowed[1].rule_pattern}."
                    )
                    errors.append([path, error_message])
                    denied_paths.append(path)
                    return successed, denied_paths, errors
                items_values = list(dict.fromkeys(items_values))
            except TypeError as err:
                if "unhashable type: 'dict'" in str(err):
                    error_message = (
                        f"Failed to make unique: dictionaries found in list at '{path}'. "
                        f"Dictionaries and other mutable types cannot be used with the [:unique:] modifier because they are unhashable. "
                        f"Encountered error while processing rule: {allowed[1].rule_pattern}."
                    )
                    errors.append([path, error_message])
                    denied_paths.append(path)
                    return successed, denied_paths, errors
                
        self.patch_value(store.old_data, path, items_values)
        successed.append(path)
        return successed, denied_paths, errors

    def apply(self, old_data, new_data):
        # First validation is check if same type, otherwise raise error
        if isinstance(old_data, list) != isinstance(new_data, list):
            old_data_type = type(old_data).__name__
            new_data_type = type(new_data).__name__
            raise TypeError(f"The data and the patch must have the same types. old_data={old_data_type}, new_data={new_data_type}")

        store = PatchingStore(
            old_data=pydash.clone_deep(old_data),
            new_data=pydash.clone_deep(new_data),
        )

        # Fix when need to setup empty values
        if not store.new_data and isinstance(store.new_data, list):
            store.new_data = [EMPTY_ARRAY_SYMBOL]

        results = self.verify_permission(list(self.get_paths(store.new_data)), self.rules)

        errors = []
        successed = []
        denied_paths = []

        for path, allowed in results.items():
            successed, denied_paths, errors = self.item_checker(
                path,
                allowed,
                store,
                successed,
                denied_paths,
                errors
            )

        return PatchResult(
            errors=errors,
            patched_data=store.old_data,
            is_patched=len(denied_paths) == 0,
            denied_paths=denied_paths,
            successed_paths=successed
        )


def patch_rules(rules):
    jsonpatch = JsonPatchRules(rules)
    return jsonpatch