import re
import enum


class ChangedData:
    """
    Class for storing added/deleted row data
    obj.added a list of all the additions, as tuple pairs: row number (int), and number of consecutive rows added
    obj.deleted a list of all the deletions, as tuple pairs: row number (int), and number of consecutive rows deleted
    """
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
    """
    Returns a ChangedData object with added/deleted row data for the diff in 'string'
    :param string: str of the diff
    :return: util.ChangedData object with:
             obj.added a list of all the additions, as tuple pairs: row number (int), and number of consecutive rows
             added
             obj.deleted a list of all the deletions, as tuple pairs: row number (int), and number of consecutive rows
             deleted
    """
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
                if code == "":
                    pass
                elif code[0] == '+':
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

def smallest_enclosing_scope(string, added):
    """
    Finds the smallest enclosing scope of the code in 'string', using the row number in 'added'
    :param string: java code as a str
    :param added: a list of two values: row number (int), and number of consecutive rows added
    :return: a list of two values: the row number (int) of the start of the enclosing scope, the row number (int) of
    the end of the enclosing scope,
    """
    enclosing_scope_lines = [0, 0]
    method_sig_re = re.compile(r"(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)" +
                               r"(?:\s*throws [\w.]+(?:\s*,\s*[\w.]+)*)?\s*\{")
    bracket_re = re.compile(r"\{|\}")

    string_split = string.splitlines()
    matches = method_sig_re.finditer('\n'.join(string_split[:added[0]]))
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

def is_added_a_whole_enclosing_scope(string, added):
    """
    If the 'added' chunk is a whole enclosing scope - e.g. a added an entire new method
    :param string: the code
    :param added: list of 2 ints, the added line and the number of lines in the chunk
    :return: True if 'added' chunk is a whole enclosing scope, False otherwise
    """
    local_added = list(added)
    decorator_re = re.compile(r"^\s*@[a-zA-Z]\w*\s*$")
    string_split = string.splitlines()
    # strip blank lines
    for i in range(added[0] - 1, added[0] + added[1]):
        if string_split[i].strip() == '':
            local_added[0] += 1
            local_added[1] -= 1
        else:
            break
    for i in range(local_added[0] - 1 + local_added[1] - 1, local_added[0] - 1, -1):
        if string_split[i].strip() == '':
            local_added[1] -= 1
        else:
            break

    if decorator_re.match(string_split[local_added[0] - 1]):
        # skip over decorators (e.g. @Test)
        local_added[0] += 1
        local_added[1] -= 1
    try:
        enclosing_scope = smallest_enclosing_scope(string, local_added)
        return local_added == enclosing_scope
    except ValueError:
        return False

def merge_two_dicts(x, y):
    """
    Merge two dictionaries and returns the result
    :param x: dictionary
    :param y: dictionary
    :return: the merged dictionary
    """
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z
