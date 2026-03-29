import yaml

def load_yaml(path: str):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge two dictionaries.
    Values in override take precedence.
    """
    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result
