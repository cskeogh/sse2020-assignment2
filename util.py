import re
import enum


class ChangedData:
    def __init__(self):
        self._added = []
        self._deleted = []

    @property
    def added(self):
        return self._added

    @added.setter
    def added(self, x):
        self._added = x

    @property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, x):
        self._deleted = x

def added_deleted_from_diff(string):
    pos_re = re.compile(r'\@\@ -(?P<origstart>\d+),(?P<origcount>\d+) \+(?P<newstart>\d+),(?P<newcount>\d+) \@\@')
    file_re = re.compile(r'diff .*\nindex .*\n\-\-\- a/(?P<origfile>.+)\n\+\+\+ b/(?P<newfile>.+)\n')

    class CodeModes(enum.Enum):
        UNCHANGED = 1
        ADDED = 2
        DELETED = 3

    def code_parse(code_lines, origstart, newstart):
        retval = ChangedData()
        code_iter = iter(code_lines)
        orig_row_count = origstart - 1  # the @@ -30,6 +30,7 @@ don't include the code on the same line as the @@
        new_row_count = newstart - 1
        block_count = 0
        mode = CodeModes.UNCHANGED
        try:
            while True:
                code = next(code_iter)
                if code[0] == '+':
                    if mode == CodeModes.UNCHANGED:
                        block_count = 1
                        mode = CodeModes.ADDED
                    elif mode == CodeModes.ADDED:
                        block_count += 1
                    elif mode == CodeModes.DELETED:
                        retval.deleted.append((orig_row_count - block_count, block_count))
                        mode = CodeModes.ADDED
                        block_count = 1
                    new_row_count += 1
                elif code[0] == '-':
                    if mode == CodeModes.UNCHANGED:
                        block_count = 1
                        mode = CodeModes.DELETED
                    elif mode == CodeModes.ADDED:
                        retval.added.append((new_row_count - block_count, block_count))
                        mode = CodeModes.ADDED
                        block_count = 1
                    elif mode == CodeModes.DELETED:
                        block_count += 1
                    orig_row_count += 1
                elif code[0] == ' ':
                    if mode == CodeModes.UNCHANGED:
                        block_count = 1
                    elif mode == CodeModes.ADDED:
                        retval.added.append((new_row_count - block_count, block_count))
                        mode = CodeModes.UNCHANGED
                        block_count = 1
                    elif mode == CodeModes.DELETED:
                        retval.deleted.append((orig_row_count - block_count, block_count))
                        mode = CodeModes.UNCHANGED
                        block_count = 1
                    orig_row_count += 1
                    new_row_count += 1
        except StopIteration:
            pass
        return retval

    def diff_parse(diff_str, new_filename):
        diff_iter = iter(pos_re.split(diff_str))
        retval = ChangedData()
        try:
            while True:
                chunk = next(diff_iter)
                if chunk == '':
                    chunk = next(diff_iter)
                orig_start = int(chunk)
                orig_count = int(next(diff_iter))
                new_start = int(next(diff_iter))
                new_count = int(next(diff_iter))
                code_lines = next(diff_iter).splitlines()
                new_delete_lines = code_parse(code_lines, orig_start, new_start)
                retval.added += new_delete_lines.added
                retval.deleted += new_delete_lines.deleted
        except StopIteration:
            pass
        return retval

    def file_parse(file_str):
        retval = {}
        file_iter = iter(file_re.split(file_str))
        try:
            while True:
                chunk = next(file_iter)
                if chunk == '':
                    chunk = next(file_iter)
                old_filename = chunk
                new_filename = next(file_iter)
                diff_str = next(file_iter)

                retval[new_filename] = diff_parse(diff_str, new_filename)
        except StopIteration:
            pass
        return retval

    return file_parse(string)

def smallest_enclosing_scope(string, line_number):
    enclosing_scope_lines = [0, 0]
    #method_sig_re = re.compile(r"(\@\S+\s*\n)?\s*(public|protected|private|static) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)(?:\s*throws [\w.]+)?\s*\{")
    method_sig_re = re.compile(r"(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)(?:\s*throws [\w.]+)?\s*\{")
    bracket_re = re.compile(r"\{|\}")

    matches = method_sig_re.finditer('\n'.join(string.splitlines()[:line_number]))
    closest_method_sig = None
    for closest_method_sig in matches:
        pass
    if closest_method_sig is None:
        raise ValueError("No enclosing scope found")
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

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z
