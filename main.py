import git
import os
import os.path
import re
import util
import datetime
import pprint

remote_link = "https://github.com/apache/cxf.git"
local_link = "repo/cxf"
the_fixing_commit = "9deb2d17"

class Progress(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(self._cur_line)


def assignment2():
    """
    Assignment 2 Vulnerability-Contributing Commits (VCCs) analysis
    :return: None
    """
    if os.path.isdir(local_link):
        print(local_link + " already exists. Skipping git clone")
    else:
        git.Repo.clone_from(remote_link, local_link, progress=Progress())
    repo = git.Repo(local_link)
    added_deleted = find_added_deleted_lines(repo, the_fixing_commit)
    deleted_commits = assignment2_part3a(repo, the_fixing_commit, added_deleted)
    added_commits = assignment2_part3b(repo, the_fixing_commit, added_deleted)
    vcc = assignment2_part3c(deleted_commits, added_commits)

    # the VCC identified here is just a code refactoring commit
    # return assignment part3a, part3b again to search for the real VCC
    added_deleted = find_added_deleted_lines(repo, vcc)
    deleted_commits = assignment2_part3a(repo, vcc, added_deleted)
    added_commits = assignment2_part3b(repo, vcc, added_deleted)
    vcc = assignment2_part3c(deleted_commits, added_commits)

    # the frequently identified commit ec3b57090cc (identified in 32 rows) is not actually the VCC
    # the VCC is: 42d3104c050. This VCC was identified as the 2nd most frequently identified commit (identified in 6
    # rows). The important code line in 42d3104c050 is reproduced below:
    # AbstractAtomProvider.java (Sergey Beryozkin 2009-11-25 12:48:57 +0000 85)         Document<T> doc = ATOM_ENGINE.getParser().parse(is);
    vcc = '42d3104c050'
    added_deleted = find_added_deleted_lines(repo, vcc)

    assignment2_part5a(repo, vcc)
    assignment2_part5b(repo, vcc)
    assignment2_part5c(repo, vcc)
    totals = assignment2_part5de(repo, vcc)
    assignment2_part5fg(repo, vcc, totals)
    assignment2_part5h(repo, vcc, added_deleted)
    assignment2_part5i(repo, vcc, added_deleted)
    all_authors = assignment2_part5j(repo, vcc, added_deleted)
    assignment2_part5k(repo, all_authors)

def find_added_deleted_lines(repo, fixing_commit):
    """
    Finds the added and deleted lines for a commit from a git repository
    :param repo: the git repository
    :param fixing_commit: string of the hash of the fixing commit
    :return: util.ChangedData object with:
             obj.added a list of all the additions, as tuple pairs: row number (int), and number of consecutive rows
             added
             obj.deleted a list of all the deletions, as tuple pairs: row number (int), and number of consecutive rows
             deleted
    """
    show_data = git_output = repo.git.show(fixing_commit, '--format=format:')
    return util.added_deleted_from_diff(show_data)

def assignment2_part3a(repo, fixing_commit, added_deleted):
    """
    Assignment part 3a: lines deleted, last commit that modified
    :param repo: the git repository
    :param fixing_commit: string of the hash of the fixing commit
    :param added_deleted: util.ChangedData object with all the added/deleted row data
    :return: a dictionary of the frequently identified commits for the deleted rows.
             Keys: git hashes, value: number of occurrences
    """
    print("\nPart 3.a -- lines deleted, last commit that modified --")
    frequently_identified_commit = {}

    for filename in added_deleted:
        filename_printed = False
        for deleted in added_deleted[filename].deleted:
            if not filename_printed:
                print(filename)
                filename_printed = True
            blame_data = repo.git.blame("-L" + str(deleted[0]) + ",+" + str(deleted[1]), fixing_commit + "^", "--",
                                        filename)
            for line in blame_data.splitlines():
                commit_id = line.split(' ')[0]
                if frequently_identified_commit.get(commit_id) is None:
                    frequently_identified_commit[commit_id] = 1
                else:
                    frequently_identified_commit[commit_id] += 1
                print(line)
    return frequently_identified_commit


def assignment2_part3b(repo, fixing_commit, added_deleted):
    """
    Assignment part 3b: lines added, last commit that modified
    :param repo: the git repository
    :param fixing_commit: string of the hash of the fixing commit
    :param added_deleted: util.ChangedData object with all the added/deleted row data
    :return: a dictionary of the frequently identified commits for the added rows.
             Keys: git hashes, value: number of occurrences
    """
    print("\nPart 3.b -- lines added, smallest enclosing scope ---------------------")
    frequently_identified_commit = {}

    for filename in added_deleted:
        filename_printed = False
        fixing_commit_contents = repo.git.show(fixing_commit + ":" + filename)
        vcc_contents = repo.git.show(fixing_commit + "^" + ":" + filename)
        for added in added_deleted[filename].added:
            if util.is_added_a_whole_enclosing_scope(fixing_commit_contents, added):
                # skip over additions 'added' chunk is a whole enclosing scope - e.g. a added an entire new method
                continue
            if not filename_printed:
                print(filename)
                filename_printed = True
            try:
                enclosing_scope_lines = util.smallest_enclosing_scope(vcc_contents, added)
                blame_data = repo.git.blame("-L" + str(enclosing_scope_lines[0]) + ",+" + str(enclosing_scope_lines[1]),
                                            fixing_commit + "^", "--", filename)

                for line in blame_data.splitlines():
                    commit_id = line.split(' ')[0]
                    if frequently_identified_commit.get(commit_id) is None:
                        frequently_identified_commit[commit_id] = 1
                    else:
                        frequently_identified_commit[commit_id] += 1
                    print(line)
            except ValueError:
                pass
    return frequently_identified_commit

def assignment2_part3c(deleted_commits, added_commits):
    """
    Assignment part 3c: frequently identified commit as the VCC
    :param deleted_commits: a dictionary of the frequently identified commits for the deleted rows.
                            Keys: git hashes, value: number of occurrences
    :param added_commits: a dictionary of the frequently identified commits for the added rows.
                            Keys: git hashes, value: number of occurrences
    :return: string of the hash of the vcc
    """
    print("\nPart 3.c -- frequently identified commit as the VCC ---------------------")
    frequently_identified_commits = util.merge_two_dicts(deleted_commits, added_commits)

    vcc = max(frequently_identified_commits, key=frequently_identified_commits.get)
    print(vcc + ' (identified in ' + str(frequently_identified_commits[vcc]) + ' rows)')
    return vcc


def assignment2_part5a(repo, vcc):
    """
    Assignment part 5a: message and title of VCC
    :param repo: the git repository
    :param vcc: string of the hash of the vcc
    :return: None
    """
    print("\nPart 5.a -- message and title of VCC ---------------------")
    git_output = repo.git.show(vcc, "-s")
    print(git_output)


def assignment2_part5b(repo, vcc):
    """
    Assignment part 5b: total files affected by VCC
    :param repo: the git repository
    :param vcc: string of the hash of the vcc
    :return: None
    """
    print("\nPart 5.b -- total files affected by VCC ---------------------")
    git_output = repo.git.show(vcc, "--stat=9999")
    print(git_output)
    match = next(re.finditer(r'(?P<filechanged>\d+) files changed', git_output))
    if match is not None:
        print(match.group('filechanged') + " files changed")


def assignment2_part5c(repo, vcc):
    """
    Assignment part 5c: total directories affected by VCC
    :param repo: the git repository
    :param vcc: string of the hash of the vcc
    :return: None
    """
    print("\nPart 5.c -- total directories affected by VCC ---------------------")
    git_output = repo.git.show(vcc, '--stat=9999', '--format=format:')
    git_output = '\n'.join(git_output.splitlines()[:-1]) # drop the last line because it's a summary line
    print(git_output)
    dirs = {}
    for filename_match in re.finditer(r'^\s*(?P<filename>[\w\\\/\.]+)', git_output, re.MULTILINE):
        dirname = os.path.dirname(filename_match.group('filename'))
        if dirs.get(dirname) is None:
            dirs[dirname] = 1
        else:
            dirs[dirname] += 1
    print(str(len(dirs.keys())) + " directories affected.")


def assignment2_part5de(repo, vcc):
    """
    Assignment part 5d: total deleted lines of code (including comments and blank lines)
    Assignment part 5e: total added lines of code (including comments and blank lines)
    :param repo: the git repository
    :param vcc: string of the hash of the vcc
    :return: dictionary with key: 'del' value: total deleted lines of code
                             key: 'add' value: total added lines of code
    """
    print("\nPart 5.d -- total deleted lines of code (including comments and blank lines) ---------------------")
    print("Part 5.e -- total added lines of code (including comments and blank lines) -------------------------")
    git_output = repo.git.show(vcc, '--numstat', '--format=format:')
    print(git_output)
    totals = {'del': 0, 'add': 0}
    for match in re.finditer(r'^\s*(?P<add>\d+)\s+(?P<del>\d+)\s', git_output, re.MULTILINE):
        totals['del'] += int(match.group('del'))
        totals['add'] += int(match.group('add'))
    print(str(totals['del']) + " total deleted lines of code (including comments and blank lines)")
    print(str(totals['add']) + " total added lines of code (including comments and blank lines)")
    return totals

def assignment2_part5fg(repo, vcc, totals):
    """
    Assignment part 5f: total deleted lines of code (excluding comments and blank lines)
    Assignment part 5g: total added lines of code (excluding comments and blank lines)
    :param repo: the git repository
    :param vcc: string of the hash of the vcc
    :param totals: dictionary with key: 'del' value: total deleted lines of code
                             key: 'add' value: total added lines of code
    :return: None
    """
    print("\nPart 5.f -- total deleted lines of code (excluding comments and blank lines) ---------------------")
    print("Part 5.g -- total added lines of code (excluding comments and blank lines) -------------------------")
    git_output = repo.git.show(vcc, '--format=format:')
    for match in re.finditer(r'^\-\s*$', git_output, re.MULTILINE):  # deleted blank lines
        totals['del'] -= 1
    for match in re.finditer(r'^\-\s*\\\\', git_output, re.MULTILINE):  # deleted comment lines
        totals['del'] -= 1
    for match in re.finditer(r'^\+\s*$', git_output, re.MULTILINE):  # added blank lines
        totals['add'] -= 1
    for match in re.finditer(r'^\+\s*\\\\', git_output, re.MULTILINE):  # added comment lines
        totals['add'] -= 1
    print(str(totals['del']) + " total deleted lines of code (excluding comments and blank lines)")
    print(str(totals['add']) + " total added lines of code (excluding comments and blank lines)")


def assignment2_part5h(repo, vcc, added_deleted):
    """
    Assignment part 5h: days were between the current VCC and the previous commit
    :param repo: the git repository
    :param vcc: string of the hash of the VCC
    :param added_deleted: util.ChangedData object with all the added/deleted row data
    :return: None
    """
    print("\nPart 5.h -- days were between the current VCC and the previous commit  ---------------------")
    for file in added_deleted.keys():
        git_output = repo.git.log(vcc, '-s', '--format=%aI', '--', file)
        if git_output.strip() == '':
            print(file + " is an added file. No previous commit available")
            continue
        else:
            print(file)
        git_output = git_output.splitlines()[:2]
        date_new = datetime.datetime.fromisoformat(git_output[0])
        date_old = datetime.datetime.fromisoformat(git_output[1])
        timedelta = date_new - date_old
        print(str(timedelta.days) + " days")


def assignment2_part5i(repo, vcc, added_deleted):
    """
    Assignment part 5i: number of times has each affected file of the current VCC been modified in the past
    :param repo: the git repository
    :param vcc: string of the hash of the VCC
    :param added_deleted: util.ChangedData object with all the added/deleted row data
    :return: None
    """
    print("\nPart 5.i -- number of times has each affected file of the current VCC been modified in the past -----")
    for file in added_deleted.keys():
        git_output = repo.git.log(vcc, '-s', '--oneline', '--', file)
        if git_output.strip() == '':
            print(file + " is an added file. No previous commit available")
            continue
        else:
            print(file)
        print(git_output)
        number_times = len(git_output.splitlines())
        print(str(number_times) + " times")

def assignment2_part5j(repo, vcc, added_deleted):
    """
    Assignment part 5j: which developers have modified each affected file since its creation
    :param repo: the git repository
    :param vcc: string of the hash of the VCC
    :param added_deleted: util.ChangedData object with all the added/deleted row data
    :return: a dictionary of all authors. Keys: author's name, value: None
    """
    print("\nPart 5.j -- Which developers have modified each affected file since its creation -----")
    all_authors = {}
    for file in added_deleted.keys():
        print(file)
        git_output = repo.git.log(vcc, '-s', '--format=%an', '--', file)
        auths = {}
        for auth in git_output.splitlines():
            if auths.get(auth) is None:
                auths[auth] = 1
            else:
                auths[auth] += 1
            all_authors[auth] = None
        for auth in auths.keys():
            print(auth + " (" + str(auths[auth]) + " commits)")
    return all_authors

def assignment2_part5k(repo, all_authors):
    """
    Assignment part 5k: For each developer, how many commits have each of them submitted
    :param repo: the git repository
    :param all_authors: a dictionary of all authors. Keys: author's name, value: None
    :return: None
    """
    print("\nPart 5.k -- For each developer, how many commits have each of them submitted -----")
    git_output = repo.git.shortlog('--summary', '--numbered', '--all', '--no-merges')
    for auth in all_authors.keys():
        for match in re.finditer(r'(?P<num>\d+)\s+(?P<name>' + re.escape(auth) + ')', git_output):
            print(match.group('name') + ' has ' + match.group('num') + ' commits')

if __name__ == '__main__':
    print('Secure Software Engineering COMP SCI 4412 Assignment 2')
    assignment2()
