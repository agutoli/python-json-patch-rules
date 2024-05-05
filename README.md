# python-json-patch-rules

Json Patch Rules is a Python library designed to facilitate the application of JSON patch operations while enforcing customizable validation rules. This library ensures that updates to JSON objects adhere to predefined permissions, making it ideal for systems that require granular access control.

## Features

- **Rule-Based Validation**: Define rules that specify which paths in a JSON object are allowed to be updated.
- **Wildcard Support**: Use wildcards to specify rules for dynamic keys and array indices.
- **Data Integrity**: Ensure that only permitted paths can be updated, preserving the integrity of the JSON structure.

## Installation

Install Json Patch Rules using pip:

```bash
pip install python-json-patch-rules
```

## API

| Rule                        | Description                                                                                       |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| `{*}`                       | Implicit set - allows to set new attributes but not remove them.                                  |
| `!{*}`                      | Implicit set - denies the ability to set new attributes.                                          |
| `[0]`                       | Implicit set - allows replacing index "0" with any value (string, object, int, etc).              |
| `[0]\|replace`               | Allows replacing index "0" with any value (string, object, int, etc).                             |
| `[*]\|unique`                | Allows replacing an array but denies if there are duplicated items (works only for arrays of strings). |
| `user`                      | Allows setting value to user property (must be an object at root level).                          |
| `!user`                     | Denies setting value to user property (must be an object at root level).                          |
| `[0].title`                 | Allows setting new value for properties (in this case title).                                     |
| `[0].nested.foo`            | Allows setting new value for property nested but will fail if not object type.                    |
| `user.contacts[0].phone`    | Allows setting user contacts but only if array index 0 and only property phone.                   |
| `user.contacts[0].label`    | Allows setting user contacts but only if array index 0 and only property label.                   |
| `user.contacts[*].label`    | Allows setting property label to any index inside contacts array.                                 |
| `bar.key1.b`                | Allows to set "foo.key1.b" only.                                                                  |
| `!bar.key1.b`               | Denies to set "foo.key1.b" only.                                                                  |


### Expanded Example Scenario

Let's imagine a more complex JSON structure representing a user profile, including nested objects for personal details, permissions, and an array of contact methods.

```python

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
            {"type": "home", "number": "1234567890", "label": "Home Phone"},
            {"type": "work", "number": "0987654321", "label": "Work Phone"}
        ]
    }
}

# Define rules to specify allowed updates
rules = [
    "!user.permissions.delete",       # Denies deletion of the delete permission under user permissions
    "user.name",                      # Allows replacing the name attribute under user
    "user.contacts[0].number",        # Allows replacing the phone number in the first contact
    "user.contacts[*].label",         # Allows updating label for any contact in the contacts array
]

# Initialize patch rules
patch = patch_rules(rules)

# Define new data to apply
new_data = {
    "user": {
        "name": "Jane Doe",
        "permissions": {
            "edit": False,
            "delete": True  # This update will be denied by the rule
        },
        "contacts": [
            {"number": "1111111111"},  # Allowed update
            {"label": "Emergency Phone"}  # Allowed update
        ]
    }
}

# Apply the patch
result = patch.apply(data, new_data)

# Output the updated JSON object
print("Patched Data:", result.data) # patched data
print("Denied Paths:", result.denied_paths) # Denied Paths: ['user.permissions.edit', 'user.permissions.delete']
print("Successed Paths:", result.successed_paths) # Successed Paths: ['user.name', 'user.contacts[0].number', 'user.contacts[1].label']
```

### Explaining the Code

#### Initializing the Json Patch Rules Library

- **Importing the Library**:
  ```python
  from json_patch_rules import patch_rules
  ```
  This line imports the `patch_rules` function from the Json Patch Rules library, making it available to use in the script.

#### Defining the Data Structure

- **JSON Data (`data`)**:
  ```python
  data = {
      "user": {
          "name": "John Doe",
          "email": "john@example.com",
          "permissions": {
              "edit": True,
              "delete": False
          },
          "contacts": [
              {"type": "home", "number": "1234567890", "label": "Home Phone"},
              {"type": "work", "number": "0987654321", "label": "Work Phone"}
          ]
      }
  }
  ```
  This JSON object represents a structured user profile with personal details, permissions, and contacts. Each contact is detailed with a type, number, and label.

#### Setting Up the Rules

- **Rules Definition (`rules`)**:
  ```python
  rules = [
      "!user.permissions.delete",
      "user.name",
      "user.contacts[0].number",
      "user.contacts[*].label",
  ]
  ```
  Here, we define a list of strings where each string is a rule that governs how the JSON data can be updated:
  - `"!user.permissions.delete"` denies any changes to the `delete` permission.
  - `"user.name"` allows changes to the user's name.
  - `"user.contacts[0].number"` allows changes to the number of the first contact.
  - `"user.contacts[*].label"` allows changes to the label of any contact in the contacts array.

#### Initializing Patch Rules

- **Patch Initialization (`patch`)**:
  ```python
  patch = patch_rules(rules)
  ```
  This creates a new instance of patch rules using the defined rules. This instance will be used to apply changes to the JSON data according to the specified rules.

#### Defining New Data for Updates

- **New Data (`new_data`)**:
  ```python
  new_data = {
      "user": {
          "name": "Jane Doe",
          "permissions": {
              "edit": False,
              "delete": True
          },
          "contacts": [
              {"number": "1111111111"},
              {"label": "Emergency Phone"}
          ]
      }
  }
  ```
  Specifies the proposed changes, including updates to the user's name, permissions, and contact details. According to the rules, the change to the `delete` permission will be denied.

#### Applying the Patch

- **Applying the Patch (`result`)**:
  ```python
  result = patch.apply(data, new_data)
  ```
  The `apply` method is called on the `patch` object with the original data and the new data. It processes each change against the established rules, applying allowed updates and blocking prohibited ones.

#### Result Analysis

- **Output Results**:
  ```python
  print("Patched Data:", result.data)
  print("Denied Paths:", result.denied_paths)
  print("Successed Paths:", result.successed_paths)
  ```
  After applying the patch, this section prints the updated JSON data, paths of denied updates, and paths of successful updates. This feedback helps validate that the Json Patch Rules library is effectively controlling data modifications according to the defined rules.


The `result` object will contain details about the operation, including which paths were updated successfully and which were denied.

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, and suggest features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
