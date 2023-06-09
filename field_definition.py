class FieldDefinition:
    def __init__(self, name, size):
        self.name = name
        self.size = size

def compare_actual_to_expected(field_label, actual, expected, warn_only=False):
    comp_result = actual == expected
    error_label = "Error"
    if warn_only:
        error_label = "Warning"

    if not comp_result:
        print(f"  ➡  {field_label}: ✖")
        print(f"     {error_label}: Invalid {field_label} [Actual, Expected] [{actual}, {expected}]")
    else:
        print(f"  ➡  {field_label}: ✔\t[{actual}:{type(actual)}]")
    return comp_result