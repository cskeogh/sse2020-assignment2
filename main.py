import git
import os
import os.path
import re

remote_link = "https://github.com/apache/cxf.git"
local_link = "repo/cxf"
fixing_commit = "9deb2d179758d3da47ce3ea492c2606c0a6a8475"
affected_files = \
    ["rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java",
     "rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java"]


class Progress(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(self._cur_line)


def assignment2():
    if os.path.isdir(local_link):
        print(local_link + " already exists. Skipping git clone")
    else:
        git.Repo.clone_from(remote_link, local_link, progress=Progress())
    repo = git.Repo(local_link)
    assignment2_part3b(repo)


def assignment2_part3a(repo):
    print("Part 3.a -- lines deleted, last commit that modified --")
    blame_data = repo.git.blame("-L92,+1", fixing_commit + "^", "--", affected_files[0])
    for line in blame_data.splitlines():
        print(line)
    blame_data = repo.git.blame("-L95,+1", fixing_commit + "^", "--", affected_files[0])
    for line in blame_data.splitlines():
        print(line)


def assignment2_part3b(repo):
    print("Part 3.b -- lines added, smallest eclosing scope --")
    added_line = 92
    enclosing_scope_lines = [0, 0]
    method_sig_re = re.compile(r"(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)(?:\s*throws [\w.]+)?\s*\{")
    bracket_re = re.compile(r"\{|\}")

    raw_data = repo.git.show(fixing_commit + ":" + affected_files[0])
    matches = method_sig_re.finditer('\n'.join(raw_data.splitlines()[:added_line]))
    closest_method_sig = None
    for closest_method_sig in matches:
        pass
    enclosing_scope_lines[0] = raw_data.count('\n', 0, closest_method_sig.start()) + 1

    matches = bracket_re.finditer(raw_data, closest_method_sig.end())
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

    enclosing_scope_lines[1] = raw_data.count('\n', closest_method_sig.start(), end_method_sig.end()) + 1
    blame_data = repo.git.blame("-L" + str(enclosing_scope_lines[0]) + ",+" + str(enclosing_scope_lines[1]),
                                fixing_commit, "--", affected_files[0])
    for line in blame_data.splitlines():
        print(line)


if __name__ == '__main__':
    print('Assignment 2')
    assignment2()
