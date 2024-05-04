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

    # Constants for regex patterns
    PATTERN_WILDCARD_ANY = r'.*'
    PATTERN_WILDCARD_ANY_KEY = r'[^.]+(?:\.[^.]+)*'
    PATTERN_WILDCARD_ANY_INDEX = r'\[\d+\]'

    def __init__(self, rules) -> None:
        self.rules = [self.parse_rule(rule) for rule in rules]

    def parse_rule(self, rule: str) -> RuleItem:
        deny = rule.startswith('!')
        new_rule = rule[1:] if deny else rule
        parts = new_rule.split('|')
        
        path = parts[0]
        path = path.replace('*', self.PATTERN_WILDCARD_ANY)
        path = path.replace('{*}', self.PATTERN_WILDCARD_ANY_KEY)
        path = path.replace('[*]', self.PATTERN_WILDCARD_ANY_INDEX)

        actions = set(parts[1:]) if len(parts) > 1 else {'replace', 'set'}
        pattern = re.compile(f'^{path}$')
        return RuleItem(rule=rule, path=path, actions=actions, deny=deny, pattern=pattern)

    def verify_permission(self, data_path: str, action: str, new_value: Any) -> bool:
        for rule in self.rules:
            # It is trying to replace the root value with a new object
            if self.TOKEN_KEY_REPLACE == rule.rule:
                if isinstance(new_value, dict):
                    return True

        return any(
            rule.pattern.match(data_path) and action in rule.actions and not rule.deny
            for rule in self.rules
        )

    def apply(self, old_data, new_data):
        return self.merge_changes(old_data, new_data)

    def apply_patch(self, data, path, value, action):
        if self.verify_permission(path, action, value):
            pydash.set_(data, path, value)
        else:
            print(f"Permission denied for action '{action}' on path '{path}'.")

    def merge_changes(self, old_data, new_data, path=''):
        for key, new_value in new_data.items():
            current_path = f"{path}.{key}" if path else key
            if self.verify_permission(current_path, 'replace', new_value):
                pydash.set_(old_data, current_path, new_value)
            else:
                old_value = pydash.get(old_data, current_path)
                action = 'replace' if old_value is not None else 'set'
                self.apply_patch(old_data, current_path, new_value, action)
        return old_data

def patch_rules(rules):
    return JsonPatchRules(rules)
