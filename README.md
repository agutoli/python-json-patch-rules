# JsonPatchRules

JsonPatchRules is a Python library designed to facilitate the application of JSON patch operations while enforcing customizable validation rules. This library ensures that updates to JSON objects adhere to predefined permissions, making it ideal for systems that require granular access control.

## Features

- **Rule-Based Validation**: Define rules that specify which paths in a JSON object are allowed to be updated.
- **Wildcard Support**: Use wildcards to specify rules for dynamic keys and array indices.
- **Data Integrity**: Ensure that only permitted paths can be updated, preserving the integrity of the JSON structure.

## Installation

Install JsonPatchRules using pip:

```bash
pip install jsonpatchrules
```

### Expanded Example Scenario

Let's imagine a more complex JSON structure representing a user profile, including nested objects for personal details, permissions, and an array of contact methods.

```python
from jsonpatchrules import patch_rules

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
            {"type": "work", "number": "0987654321"}
        ]
    }
}

# Define rules to specify allowed updates
rules = [
    "user.{name,email}",  # Allow updates to both the name and email
    "user.permissions.*",  # Allow updates to any permissions fields
    "user.contacts[*].number"  # Allow updates to the phone number in any contact
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
            {"type": "home", "number": "1111111111"},  # This update is allowed
            {"type": "work", "number": "2222222222"}  # This update is allowed
        ]
    }
}

# Apply the patch
result = patch.apply(data, new_data)

# Output the updated JSON object
print("Patched Data:", result.patched_data)
print("Denied Paths:", result.denied_paths)
print("Successed Paths:", result.successed_paths)
```

### Explanation of This Example

1. **Complex JSON Structure**: The `data` dictionary includes nested objects and arrays, reflecting a realistic data structure you might encounter in applications.

2. **Diverse Rule Definitions**:
   - `"user.{name,email}"`: This rule uses curly braces `{}` to specify that both `name` and `email` fields under `user` can be updated.
   - `"user.permissions.*"`: The wildcard `*` allows changes to any fields under `permissions`, demonstrating flexibility in what can be updated without listing every possible field.
   - `"user.contacts[*].number"`: This rule demonstrates how to allow updates to specific fields within any object in an array. The `[*]` wildcard allows the operation on any element index within the `contacts` array.

3. **Patch Application and Results**: The `apply` method is used to attempt updating `data` with `new_data` based on the defined `rules`. The results show which paths were successfully updated and which were denied, although in this example, all updates conform to the rules.

This example is comprehensive, demonstrating key features of your library and providing users with a clear understanding of how to implement rule-based JSON patching in their applications.


## Usage

### Defining Rules

Rules are strings that specify the allowed paths in the JSON object:

- `"user.name"`: Allows updates to the `name` field under the `user` key.
- `"user.*"`: Allows updates to any field under `user`.
- `"array[*]"`: Allows updates to any element in `array`.

### Applying Patches

To apply a patch:

```python
patch = patch_rules(rules)
result = patch.apply(original_data, new_data)
```

The `result` object will contain details about the operation, including which paths were updated successfully and which were denied.

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, and suggest features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
