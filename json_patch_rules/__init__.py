import re
from typing import Any, Optional, Pattern, List, Set, Tuple, Generator
from dataclasses import dataclass
import pydash
from json_patch_rules.__symbols__ import EMPTY_ARRAY_SYMBOL

@dataclass
class RuleItem:
    actions: Set[str]
    current_rule: str = ''
    path: Optional[str] = None
    deny: bool = False
    pattern: Optional[Pattern[str]] = None
    parent_path: Optional[str] = None

@dataclass
class ResultData:
    data: Any

class JsonPatchRules:
    ROOT_TOKEN_REPLACE = '*|replace'
    ROOT_TOKEN_KEY = '{*}'
    ROOT_TOKEN_KEY_REPLACE = '{*}|replace'
    ROOT_TOKEN_ARRAY = '[*]'
    ROOT_TOKEN_ARRAY_REPLACE = '[*]|replace'

    PATTERN_WILDCARD_ANY = r'(?P<ANY>.*)'
    PATTERN_WILDCARD_ANY_KEY = r'(?P<ANY_KEY>.*)'
    PATTERN_WILDCARD_ANY_INDEX = r'(?P<INDEX>\[\d+\])'

    def __init__(self, rules: List[str]) -> None:
        self.rules: List[RuleItem] = [self.parse_rule(rule) for rule in rules]

    def parse_rule(self, current_rule: str) -> RuleItem:
        deny = current_rule.startswith('!')
        rule_item = RuleItem(set(), deny=deny, current_rule=current_rule)

        rule = current_rule[1:] if deny else current_rule
        parts = rule.split('|')

        path = parts[0].replace(r'\[\d\]$', '')
        path = re.sub(r'\[\*\]+$', '', path)
        path = re.sub(r'\[\d\]+$', '', path)
        path = re.sub(r'\{\*\}+$', '', path)
        rule_item.parent_path = path

        path = path.replace('{*}', self.PATTERN_WILDCARD_ANY_KEY)
        path = path.replace('[*]', self.PATTERN_WILDCARD_ANY_INDEX)

        # ATTENTION: It must be after any replace that contains "*" character
        path = path.replace('*', self.PATTERN_WILDCARD_ANY)
        actions = set(parts[1:]) if len(parts) > 1 else {'set'}
        pattern = re.compile(f'^{path}')

        rule_item.path = path
        rule_item.pattern = pattern
        rule_item.actions = actions

        return rule_item

    def to_unique(self, items: List[Any]) -> List[Any]:
        ordered_list = []
        for item in items:
            if item not in ordered_list:
                ordered_list.append(item)
        return ordered_list

    def get_paths(self, obj: Any, current_path: str = "") -> Generator[str, str, str | None]:
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

    def verify_permission(self, data_path: str, new_data: Any) -> Tuple[bool, RuleItem, Optional[str]]:
        check_all_responses = []
        for rule in self.rules:
            if self.ROOT_TOKEN_KEY == rule.current_rule and isinstance(new_data, dict):
                return (True, rule, None)
            elif self.ROOT_TOKEN_ARRAY == rule.current_rule and isinstance(new_data, list):
                return (True, rule, None)
            elif self.ROOT_TOKEN_KEY_REPLACE == rule.current_rule and isinstance(new_data, dict):
                return (True, rule, None)
            elif self.ROOT_TOKEN_ARRAY_REPLACE == rule.current_rule and isinstance(new_data, list):
                return (True, rule, None)
            elif self.ROOT_TOKEN_REPLACE == rule.current_rule and isinstance(new_data, (list, dict)):
                return (True, rule, None)

            match_result = rule.pattern and rule.pattern.match(data_path)
            allow = (match_result and not rule.deny) or data_path.startswith(rule.current_rule)
            check_all_responses.append((allow, rule, data_path))

        # Check if has at least a single allow=True
        for item in check_all_responses:
            if item[0]:
                return item

        return (False, RuleItem(set([])), None)

    def apply(self, old_data: Any, new_data: Any) -> ResultData:
        result = ResultData(pydash.clone_deep(old_data))

        actions_data = {"unique": []}
        value_obj_paths = list(self.get_paths(new_data))
        
        if len(value_obj_paths) == 0:
            value_obj_paths = [EMPTY_ARRAY_SYMBOL]

        for path in value_obj_paths:
            is_allowed, rule_item, data_path = self.verify_permission(path, new_data)
            if is_allowed:
                should_replace = 'replace' in rule_item.actions
                should_be_unique = 'unique' in rule_item.actions

                if should_replace and data_path is None:
                    result.data = new_data
                elif should_replace and data_path:
                    pydash.set_(result.data, rule_item.path, pydash.get(new_data, rule_item.path))
                elif should_be_unique:
                    new_value = pydash.get(new_data, path)
                    pydash.get(result.data, rule_item.path, []).append(new_value)
                else:
                    new_value = pydash.get(new_data, path)
                    pydash.set_(result.data, path, new_value)

                ### 1) Unique + Replace = It allows user to remove itens from array
                if should_be_unique and should_replace:
                    actions_data["unique"].append((rule_item, data_path))
                ### 2) Unique  = It add new itens to array if not exists
                elif should_be_unique and not should_replace:
                    actions_data["unique"].append((rule_item, data_path))
            else:
                print("Not allowed:", path)

        for item in actions_data["unique"]:
            rule_item, data_path = item
            current_value = pydash.get(result.data, rule_item.path)
            if isinstance(current_value, list):
                pydash.set_(result.data, rule_item.path, self.to_unique(current_value))
            elif isinstance(result.data, list): # should support all json types except list and object
                for item in new_data:
                    result.data.append(item)
                    result.data = self.to_unique(result.data)

        return result

def patch_rules(rules: List[str]) -> JsonPatchRules:
    return JsonPatchRules(rules)
