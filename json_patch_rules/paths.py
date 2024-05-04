def get_paths(obj, current_path=""):
    """ Recursively find all paths in a nested JSON object and format them in dot and bracket notation. """
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{current_path}.{k}" if current_path else k
            yield from get_paths(v, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_path = f"{current_path}[{i}]"
            yield from get_paths(v, new_path)
    else:
        yield current_path
