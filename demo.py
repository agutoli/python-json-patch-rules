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
            {"type": "work", "number": "0987654321"}
        ]
    }
}


rules = [
    "*|replace",                      # allows to replace value at root level object or array
    "!*|replace",                     # deny to replace value at root level object or array
    "{*}|replace",                    # allows to replace any object keys/values
    "!{*}|replace",                   # deny to replace any object keys/values
    "{*}",                            # implicit set - allows to set new attributes but not remove it
    "!{*}",                           # implicit set - deny to set new attributes but not remove it
    "{*}|set",                        # allows to set new attributes but not remove it
    "[0]",                            # implicit set - allows to replace index "0" with any value (string, object, int, etc)
    "[0]|string",                     # set only string type
    "[0]|string|number",              # set only string type
    "[0]|replace",                    # allows to replace index "0" with any value (string, object, int, etc)
    "[*]|unique",                     # allows to replace array but denies if duplicated items (it works only for array of strings)
    "[*]|add",                        # allows to add new items but it can't remove any existent one. 
    "[*]|add|unique",                 # allows to add new items but it will ignore if already exists. 
    "user",                           # allows to set value to user property (it must be object at root level)
    "!user",                          # deny to set value to user property (it must be object at root level)
    "[0].title",                      # allows to set new value for properties (in this case title)
    "[0].nested.foo",                 # allows to set new value for property nested but it will fail if not object type
    "user.contacts[0].phone",         # allows set user contacts but only if array 0 but only property phone
    "user.contacts[0].label",         # allows set user contacts but only if array 0 but only property label
    "user.contacts[0].{label,phone}", # allows set user contacts but only if array 0 and label and/or phone
    "user.contacts[*].label"          # allows set property label to any index inside contacts array
]

patch = patch_rules(rules)

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