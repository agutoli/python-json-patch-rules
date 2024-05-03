import json
from json_patch_rules import patch_rules

# Define a complex JSON object
data = {
    "user": {
        "name": "John Doe",
        "email": "john@example.com",
        "permissions": {
            "edit": True,
            "delete": False
        },
        "contacts": [
            {"type": "home", "number": "1234567890"},
            {"type": "home", "number": "1234567890"},
            {"type": "work", "number": "need remove this"}
        ]
    }
}

# Define rules to specify allowed updates
rules = [
    "user.contacts[:unique:]"
]

# Initialize patch rules
patch = patch_rules(rules)

# Define new data to apply
new_data = {
    "user": {
        "name": "Jane Doe",  # This update is allowed
        "email": "jane@example.com",  # This update is allowed
        "permissions": {
            "edit": False,  # This update is allowed
            "delete": True  # This update is allowed
        },
        "contacts": [
            1,  # This update is allowed
            False  # This update is allowed
        ]
    }
}

# Apply the patch
result = patch.apply(data, new_data)

# Output the updated JSON object
print("Patched Data:", json.dumps(result.patched_data, indent=2))
print("Denied Paths:", result.denied_paths)
print("Successed Paths:", result.successed_paths)
print("Errors:", result.errors)