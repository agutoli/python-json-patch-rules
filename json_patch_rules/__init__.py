import re
import pydash
from typing import Any, Optional, Pattern
from dataclasses import dataclass

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

class JsonPatchRules:
    UNIQUE_ITEMS_LIST = "$__UNIQUE_ITEMS_LIST__$"
    REPLACE_ITEMS_LIST = "$__REPLACE_ITEMS_LIST__$"

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
            '[*]': '$__INDEX_WILDCARD__$',
            '[:unique:]': self.UNIQUE_ITEMS_LIST,
            '[:replace:]': self.REPLACE_ITEMS_LIST,
            '[:uniqueBy(*):]': '$__LIST_OF_OBJECT_UNIQUE__$',
            '{*}': '$__ANY_KEY_WILDCARD__$',
            '*': '$__ANY_SEG_WILDCARD__$',
        }
        for key, value in placeholder_dict.items():
            rule = rule.replace(key, value)

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
            rule = replace_items_parts[0] # ignore all properties after [:unique:]
            rule_item.replace = True
            rule_item.unique = False
            rule_item.replace_path = replace_items_parts[0]

        # Escape the rule to safely turn into regex, then restore placeholders to regex patterns
        rule = re.escape(rule)
        rule = rule.replace(re.escape('$__INDEX_WILDCARD__$'), r'\[\d+\]')
        rule = rule.replace(re.escape('$__ANY_KEY_WILDCARD__$'), r'[^.]+')
        rule = rule.replace(re.escape('$__ANY_SEG_WILDCARD__$'), r'.+')

        # Replace {key1,key2,...} with regex alternation group
        def replace_options(match):
            options = match.group(1)
            options = '|'.join(re.escape(option.strip()) for option in options.split(','))
            return f"(?:{options})"

        rule = re.sub(r'\\{([^\\}]+)\\}', replace_options, rule)
        rule_item.compile = re.compile('^' + rule + '$')

        return rule_item

    def verify_permission(self, data_paths, permission_rules):
        """Check if the provided data paths are allowed by the permission rules."""
        rule_items = [self.parse_rule(rule) for rule in permission_rules]
        results = {}
        for path in data_paths:
            for rule_item in rule_items:
                if rule_item.replace and rule_item.replace_path:
                    results[rule_item.replace_path] = [True, rule_item]
                elif rule_item.compile:
                    results[path] = [rule_item.compile.match(path), rule_item]
                else:
                    results[path] = [False, None]
        return results

    def apply(self, data, new_data):
        cloned_data = pydash.clone_deep(data)
        results = self.verify_permission(self.get_paths(new_data), self.rules)
        denied_paths = []
        successed = []
        errors = []
        for path, allowed in results.items():
            if allowed[0]:
                if allowed[1].unique:
                    items_values = pydash.get(new_data, path)
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
                                continue
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
                                continue
                    pydash.set_(cloned_data, path, items_values)
                    successed.append(path)
                else:
                    pydash.set_(cloned_data, path, pydash.get(new_data, path))
                    successed.append(path)
            else:
                denied_paths.append(path)

        return PatchResult(
            errors=errors,
            patched_data=cloned_data,
            is_patched=len(denied_paths) == 0,
            denied_paths=denied_paths,
            successed_paths=successed
        )


def patch_rules(rules):
    jsonpatch = JsonPatchRules(rules)
    return jsonpatch