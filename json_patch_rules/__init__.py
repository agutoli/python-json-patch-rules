import re
from typing import Any, Optional, Pattern
from dataclasses import dataclass
import pydash

@dataclass
class RuleItem:
    rule: str
    path: str
    actions: set
    deny: bool = False
    pattern: Optional[Pattern[str]] = None

class JsonPatchRules:
    TOKEN_KEY_REPLACE = '{*}|replace'
    TOKEN_ROOT_REPLACE = '*|replace'
    TOKEN_ROOT_ARRAY_REPLACE = '[*]|replace'

    # Constants for regex patterns
    PATTERN_WILDCARD_ANY = r'.*'
    PATTERN_WILDCARD_ANY_KEY = r'[^.]+(?:\.[^.]+)*'
    PATTERN_WILDCARD_ANY_INDEX = r'\[\d+\]'

    def __init__(self, rules) -> None:
        self.rules = [self.parse_rule(rule) for rule in rules]

    def parse_rule(self, current_rule: str) -> RuleItem:
        deny = current_rule.startswith('!')
        rule = current_rule[1:] if deny else current_rule
        parts = rule.split('|')
        path = parts[0].replace('*', self.PATTERN_WILDCARD_ANY)
        path = path.replace('{*}', self.PATTERN_WILDCARD_ANY_KEY)
        path = path.replace('[*]', self.PATTERN_WILDCARD_ANY_INDEX)
        actions = set(parts[1:]) if len(parts) > 1 else {'replace', 'set'}
        pattern = re.compile(f'^{path}$')
        return RuleItem(rule=current_rule, path=path, actions=actions, deny=deny, pattern=pattern)

    def verify_permission(self, data_path: str, action: str, new_value: Any) -> bool | None:
        for rule in self.rules:
            # It is trying to replace the root value with a new object
            if self.TOKEN_KEY_REPLACE == rule.rule:
                if isinstance(new_value, dict):
                    return True
            if self.TOKEN_ROOT_ARRAY_REPLACE == rule.rule:
                if isinstance(new_value, list):
                    return True
            else:
                if data_path:
                    return rule.pattern.match(data_path) and action in rule.actions and not rule.deny
                return False

    def apply(self, old_data, new_data):
        return self.merge_changes(old_data, new_data)

    def apply_patch(self, data, path, value, action):
        if self.verify_permission(path, action, value):
            pydash.set_(data, path, value)
        else:
            print(path, action, value)
            print(f"Permission denied for action '{action}' on path '{path}'.")

    def merge_changes(self, old_data, new_data, path=''):
        if isinstance(old_data, list) and isinstance(new_data, list):
            # Handle array root replacement
            for i, item in enumerate(new_data):
                item_path = f"{path}[{i}]"
                if self.verify_permission(item_path, 'replace', item):
                    if i < len(old_data):
                        old_data[i] = item
                    else:
                        old_data.append(item)
                else:
                    if i < len(old_data):
                        self.merge_changes(old_data[i], item, item_path)
        elif isinstance(old_data, dict) and isinstance(new_data, dict):
            for key, new_value in new_data.items():
                current_path = f"{path}.{key}" if path else key
                if self.verify_permission(current_path, 'replace', new_value):
                    pydash.set_(old_data, current_path, new_value)
                else:
                    old_value = pydash.get(old_data, current_path)
                    self.apply_patch(old_data, current_path, new_value, 'replace' if old_value is not None else 'set')
        return old_data

def patch_rules(rules):
    return JsonPatchRules(rules)
