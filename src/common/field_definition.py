class FieldDefinition:
    def __init__(self, name, size):
        self.name = name
        self.size = size


LOG_LEVEL_QUIET = 0
LOG_LEVEL_NORMAL = 1
LOG_LEVEL_VERBOSE =2
def compare_actual_to_expected(field_label, actual, expected, log_level=LOG_LEVEL_QUIET, cb=lambda x: x):
    comp_result = actual == expected
    log = ""
    if not comp_result and log_level != LOG_LEVEL_QUIET:
        log += f"  ➡  {field_label}: ✖\n"
        if log_level == LOG_LEVEL_VERBOSE:
            log += f"      ➡  Invalid {field_label} [Actual, Expected] [{cb(actual)}, {cb(expected)}]\n"
    else:
        log += f"  ➡  {field_label}: ✔\t[{cb(actual)}:{type(actual)}]\n"
    return [comp_result,log]