import re

def smallest_enclosing_scope(string, line_number):
    enclosing_scope_lines = [0, 0]
    method_sig_re = re.compile(r"(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)(?:\s*throws [\w.]+)?\s*\{")
    bracket_re = re.compile(r"\{|\}")

    matches = method_sig_re.finditer('\n'.join(string.splitlines()[:line_number]))
    closest_method_sig = None
    for closest_method_sig in matches:
        pass
    enclosing_scope_lines[0] = string.count('\n', 0, closest_method_sig.start()) + 1

    matches = bracket_re.finditer(string, closest_method_sig.end())
    nest_levels = 0
    end_method_sig = None
    for end_method_sig in matches:
        if end_method_sig.group(0) == '{':
            nest_levels += 1
        elif end_method_sig.group(0) == '}':
            if nest_levels == 0:
                break
            else:
                nest_levels -= 1
    if end_method_sig is None:
        raise ValueError("Parse error")

    enclosing_scope_lines[1] = string.count('\n', closest_method_sig.start(), end_method_sig.end()) + 1
    return enclosing_scope_lines
