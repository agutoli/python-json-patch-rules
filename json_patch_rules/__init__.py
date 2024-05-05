import re
from dataclasses import dataclass
from typing import Any, Optional, Pattern, Tuple
from dataclasses import dataclass
import pydash

@dataclass
class RuleItem:
    actions: set
    current_rule: str = ''
    path: str | None = None
    deny: bool = False
    pattern: Optional[Pattern[str]] = None

@dataclass
class ResultData:
    data: str


class JsonPatchRules:
    ROOT_TOKEN_REPLACE = '*|replace'
    ROOT_TOKEN_KEY_REPLACE = '{*}|replace'
    ROOT_TOKEN_ARRAY_REPLACE = '[*]|replace'

    # Constants for regex patterns
    PATTERN_WILDCARD_ANY = r'.*'
    PATTERN_WILDCARD_ANY_KEY = r'[^.]+(?:\.[^.]+)*'
    PATTERN_WILDCARD_ANY_INDEX = r'\[\d+\]'

    def __init__(self, rules) -> None:
        self.rules = [self.parse_rule(rule) for rule in rules]

    def parse_rule(self, current_rule: str) -> RuleItem:
        deny = current_rule.startswith('!')

        rule_item = RuleItem(
            set([]),
            deny=deny,
            current_rule=current_rule
        )

        rule = current_rule[1:] if deny else current_rule
        parts = rule.split('|')
        
        path = parts[0].replace('*', self.PATTERN_WILDCARD_ANY)
        path = path.replace('{*}', self.PATTERN_WILDCARD_ANY_KEY)
        path = path.replace('[*]', self.PATTERN_WILDCARD_ANY_INDEX)

        actions = set(parts[1:]) if len(parts) > 1 else {'set'}

        if 'replace' in actions:
            pattern = re.compile(f'^{path}.*')
        else:
            pattern = re.compile(f'^{path}$')

        rule_item.path = path
        rule_item.pattern = pattern
        rule_item.actions = actions

        return rule_item

    def to_unique(self, items: list):
        ordered_list = []
        for item in items:
            if item not in ordered_list:
                ordered_list.append(item)
        return ordered_list

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
        elif isinstance(obj, (list, dict)):
            for i, v in enumerate(obj):
                new_path = f"{current_path}[{i}]"
                yield from self.get_paths(v, new_path)
        else:
            yield current_path

    def verify_permission(self, data_path: str, new_data: Any) -> Tuple[bool | None, RuleItem, str | None]:
        check_all_responses = []
        for rule in self.rules:
            # It is trying to replace the root value with a new object
            if self.ROOT_TOKEN_KEY_REPLACE == rule.current_rule:
                if isinstance(new_data, dict):
                    return (True, rule, None)
            elif self.ROOT_TOKEN_ARRAY_REPLACE == rule.current_rule:
                if isinstance(new_data, list):
                    return (True, rule, None)
            elif self.ROOT_TOKEN_REPLACE == rule.current_rule:
                if isinstance(new_data, (list, dict)):
                    return (True, rule, None)

            allow = (rule.pattern.match(data_path) and not rule.deny) or data_path.startswith(rule.current_rule)
            check_all_responses.append((allow, rule, data_path))

        # Check if has at least a single allow=True
        for item in check_all_responses:
            if item[0]:
                return item

        return (False, RuleItem(set([])), None)

    def apply(self, old_data: Any, new_data: Any):
        result = ResultData(pydash.clone(old_data))

        actions_data = {
            "unique": set([])
        }

        for path in self.get_paths(new_data):
            is_allowed, rule_item, data_path = self.verify_permission(path, new_data)
            if is_allowed:
                if 'replace' in rule_item.actions and data_path == None:
                    result.data = new_data
                elif 'replace' in rule_item.actions and data_path:
                    pydash.set_(result.data, rule_item.path, pydash.get(new_data, rule_item.path))
                else:
                    new_value = pydash.get(new_data, rule_item.path)
                    pydash.set_(result.data, path, new_value)
                if 'unique' in rule_item.actions:
                        actions_data["unique"].add(rule_item.path)
            else:
                print("Not allowed::", path)

        for item in actions_data["unique"]:
            pydash.set_(result.data, item, self.to_unique(pydash.get(result.data, item)))
        return result

def patch_rules(rules):
    return JsonPatchRules(rules)
