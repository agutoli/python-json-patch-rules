import re
import pydash
from typing import Any
from dataclasses import dataclass

@dataclass
class PatchResult:
    denied_paths: list[str]
    successed_paths: list[str]
    is_patched: bool
    patched_data: Any


class JsonPatchRules:
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
        """Convert a permission rule into a regex pattern for matching paths."""
        # Temporary placeholders for complex wildcards to avoid premature escaping
        placeholder_dict = {
            '[*]': 'INDEX_WILDCARD',
            '{*}': 'ANY_KEY_WILDCARD',
            '*': 'ANY_SEG_WILDCARD',
        }
        for key, value in placeholder_dict.items():
            rule = rule.replace(key, value)

        # Escape the rule to safely turn into regex, then restore placeholders to regex patterns
        rule = re.escape(rule)
        rule = rule.replace(re.escape('INDEX_WILDCARD'), r'\[\d+\]')
        rule = rule.replace(re.escape('ANY_KEY_WILDCARD'), r'[^.]+')
        rule = rule.replace(re.escape('ANY_SEG_WILDCARD'), r'.+')

        # Replace {key1,key2,...} with regex alternation group
        def replace_options(match):
            options = match.group(1)
            options = '|'.join(re.escape(option.strip()) for option in options.split(','))
            return f"(?:{options})"

        rule = re.sub(r'\\{([^\\}]+)\\}', replace_options, rule)

        return re.compile('^' + rule + '$')

    def verify_permission(self, data_paths, permission_rules):
        """Check if the provided data paths are allowed by the permission rules."""
        patterns = [self.parse_rule(rule) for rule in permission_rules]

        results = {}
        for path in data_paths:
            allowed = any(pattern.match(path) for pattern in patterns)
            results[path] = allowed
        return results

    def apply(self, data, new_data):
        results = self.verify_permission(self.get_paths(new_data), self.rules)
        denied_paths = []
        successed = []
        for path, allowed in results.items():
            if allowed:
                successed.append(path)
            else:
                denied_paths.append(path)

        cloned_data = pydash.clone_deep(data)
        for item_to_patch in successed:
            pydash.set_(cloned_data, item_to_patch, pydash.get(new_data, item_to_patch))

        return PatchResult(
            patched_data=cloned_data,
            is_patched=len(denied_paths) == 0,
            denied_paths=denied_paths,
            successed_paths=successed
        )
        # return {
        #     "has_errors": len(denied_paths) > 0,
        #     "denied": denied_paths,
        #     "success": success
        # }


def patch_rules(rules):
    jsonpatch = JsonPatchRules(rules)
    return jsonpatch


# # # Example usage
# # data_paths = [
# #     "features.ccc.test.any_other_key.data[0].one_more_key.title",
# #     "features.vvv.test.any_other_key.data[0].one_more_key.property",
# #     "features.aaa.test.any_other_key.data[0].one_more_key.title",
# #     "features.yyy.test.any_other_key.data[0].one_more_key.title"
# # ]

# # permission_rules = [
# #     "features.{ccc,vvv,aaa}.test.any_other_key.data[0].one_more_key.title",
# #     "features.{ccc,vvv,aaa}.test.any_other_key.data[0].one_more_key.property"
# # ]

# # # Validate permissions
# # results = verify_permission(data_paths, permission_rules)
# # for path, allowed in results.items():
# #     print(f"Path: {path} - {'Allowed' if allowed else 'Denied'}")
