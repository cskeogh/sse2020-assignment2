import git
import os
import os.path
import re
import util
import datetime

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
    assignment2_part3a(repo)
    frequently_identified_commit = assignment2_part3b(repo)
    vcc = assignment2_part3c(frequently_identified_commit)
    assignment2_part5a(repo, vcc)
    assignment2_part5b(repo, vcc)
    assignment2_part5c(repo, vcc)
    totals = assignment2_part5de(repo, vcc)
    assignment2_part5fg(repo, vcc, totals)
    assignment2_part5h(repo, vcc)
    assignment2_part5i(repo, vcc)
    all_authors = assignment2_part5j(repo, vcc)
    assignment2_part5k(repo, vcc, all_authors)

def assignment2_part3a(repo):
    print("\nPart 3.a -- lines deleted, last commit that modified --")
    frequently_identified_commit = {}
    blame_data = repo.git.blame("-L92,+1", fixing_commit + "^", "--", affected_files[0])
    for line in blame_data.splitlines():
        print(line)
    blame_data = repo.git.blame("-L95,+1", fixing_commit + "^", "--", affected_files[0])
    for line in blame_data.splitlines():
        commit_id = line.split(' ')[0]
        if frequently_identified_commit.get(commit_id) is None:
            frequently_identified_commit[commit_id] = 1
        else:
            frequently_identified_commit[commit_id] += 1
        print(line)
    return frequently_identified_commit

def assignment2_part3b(repo):
    print("\nPart 3.b -- lines added, smallest enclosing scope ---------------------")
    added_line = 92
    frequently_identified_commit = {}
    raw_file_contents = repo.git.show(fixing_commit + "^" + ":" + affected_files[0])
    enclosing_scope_lines = util.smallest_enclosing_scope(raw_file_contents, added_line)

    blame_data = repo.git.blame("-L" + str(enclosing_scope_lines[0]) + ",+" + str(enclosing_scope_lines[1]),
                                fixing_commit + "^", "--", affected_files[0])

    for line in blame_data.splitlines():
        commit_id = line.split(' ')[0]
        if frequently_identified_commit.get(commit_id) is None:
            frequently_identified_commit[commit_id] = 1
        else:
            frequently_identified_commit[commit_id] += 1
        print(line)
    return frequently_identified_commit

def assignment2_part3c(frequently_identified_commit):
    print("\nPart 3.c -- frequently identified commit as the VCC ---------------------")
    vcc = max(frequently_identified_commit, key=frequently_identified_commit.get)
    print(vcc)
    return vcc


def assignment2_part5a(repo, vcc):
    print("\nPart 5.a -- message and title of VCC ---------------------")
    git_output = repo.git.show(vcc, "-s")
    print(git_output)


def assignment2_part5b(repo, vcc):
    print("\nPart 5.b -- total files affected by VCC ---------------------")
    git_output = repo.git.show(vcc, "--stat=9999")
    print(git_output)
    match = next(re.finditer(r'(?P<filechanged>\d+) files changed', git_output))
    if match is not None:
        print(match.group('filechanged') + " files changed")


def assignment2_part5c(repo, vcc):
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
    print("\nPart 5.f -- total deleted lines of code (excluding comments and blank lines) ---------------------")
    print("Part 5.g -- total added lines of code (excluding comments and blank lines) -------------------------")
    git_output = repo.git.show(vcc, '--format=format:')
    print(git_output)
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


def assignment2_part5h(repo, vcc):
    print("\nPart 5.h -- days were between the current VCC and the previous commit  ---------------------")
    for file in affected_files:
        print(file)
        git_output = repo.git.log(vcc, '-s', '--format=%aI', '--', file)
        git_output = git_output.splitlines()[:2]
        print('\n'.join(git_output))
        date_new = datetime.datetime.fromisoformat(git_output[0])
        date_old = datetime.datetime.fromisoformat(git_output[1])
        timedelta = date_new - date_old
        print(str(timedelta.days) + " days")


def assignment2_part5i(repo, vcc):
    print("\nPart 5.i -- time has each affected file of the current VCC been modified in the past -----")
    for file in affected_files:
        print(file)
        git_output = repo.git.log(vcc, '-s', '--oneline', '--', file)
        print(git_output)
        number_times = len(git_output.splitlines())
        print(str(number_times) + " times")

def assignment2_part5j(repo, vcc):
    print("\nPart 5.j -- Which developers have modified each affected file since its creation -----")
    all_authors = {}
    for file in affected_files:
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

def assignment2_part5k(repo, vcc, all_authors):
    print("\nPart 5.k -- For each developer, how many commits have each of them submitted -----")
    git_output = repo.git.shortlog('--summary', '--numbered', '--all', '--no-merges')
    for auth in all_authors.keys():
        for match in re.finditer(r'(?P<num>\d+)\s+(?P<name>' + re.escape(auth) + ')', git_output):
            print(match.group('name') + ' has ' + match.group('num') + ' commits')

if __name__ == '__main__':
    print('Assignment 2')
    #assignment2()
    string = """diff --git a/rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java b/rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java
index 179ee66c16..acc1285635 100644
--- a/rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java
+++ b/rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java
@@ -30,6 +30,7 @@ import javax.ws.rs.core.MediaType;
 import javax.ws.rs.core.MultivaluedMap;
 import javax.ws.rs.ext.MessageBodyReader;
 import javax.ws.rs.ext.MessageBodyWriter;
+import javax.xml.stream.XMLStreamReader;
 
 import org.apache.abdera.Abdera;
 import org.apache.abdera.model.Document;
@@ -39,6 +40,7 @@ import org.apache.abdera.parser.ParserOptions;
 import org.apache.abdera.writer.Writer;
 import org.apache.cxf.common.logging.LogUtils;
 import org.apache.cxf.jaxrs.utils.ExceptionUtils;
+import org.apache.cxf.staxutils.StaxUtils;
 
 public abstract class AbstractAtomProvider<T extends Element> 
     implements MessageBodyWriter<T>, MessageBodyReader<T> {
@@ -89,10 +91,10 @@ public abstract class AbstractAtomProvider<T extends Element>
             ParserOptions options = parser.getDefaultParserOptions();
             if (options != null) {
                 options.setAutodetectCharset(autodetectCharset);
-                options.setResolveEntities(false);
             }
         }
-        Document<T> doc = parser.parse(is);
+        XMLStreamReader reader = StaxUtils.createXMLStreamReader(is);
+        Document<T> doc = parser.parse(reader);
         return doc.getRoot();
     }
 
diff --git a/rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java b/rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java
index 0296764b5d..025748c0de 100644
--- a/rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java
+++ b/rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java
@@ -145,6 +145,25 @@ public class AtomPojoProviderTest extends Assert {
                                             new Annotation[]{}, mt, null, bis);
         assertEquals("a", book.getName());
     }
+    @Test
+    public void testReadEntryNoBuilders2() throws Exception {
+        final String entry = 
+            "<!DOCTYPE entry SYSTEM \"entry://entry\"><entry xmlns=\"http://www.w3.org/2005/Atom\">"
+            + "<title type=\"text\">a</title>"
+            + "<content type=\"application/xml\">"
+            + "<book xmlns=\"\">"
+            + "<name>a</name>"
+            + "</book>"
+            + "</content>"
+            + "</entry>";
+        AtomPojoProvider provider = new AtomPojoProvider();
+        ByteArrayInputStream bis = new ByteArrayInputStream(entry.getBytes());
+        MediaType mt = MediaType.valueOf("application/atom+xml;type=entry");
+        @SuppressWarnings({"unchecked", "rawtypes" })
+        Book book = (Book)provider.readFrom((Class)Book.class, Book.class, 
+                                            new Annotation[]{}, mt, null, bis);
+        assertEquals("a", book.getName());
+    }
     
     
     @Test
@@ -179,6 +198,24 @@ public class AtomPojoProviderTest extends Assert {
         assertTrue("b".equals(list.get(0).getName()) || "b".equals(list.get(1).getName()));        
     }
      
+    @Test
+    public void testReadFeedWithoutBuilders2() throws Exception {
+        AtomPojoProvider provider = new AtomPojoProvider();
+        final String feed = 
+            "<!DOCTYPE feed SYSTEM \"feed://feed\"><feed xmlns=\"http://www.w3.org/2005/Atom\">"
+            + "<entry><content type=\"application/xml\"><book xmlns=\"\"><name>a</name></book></content></entry>"
+            + "<entry><content type=\"application/xml\"><book xmlns=\"\"><name>b</name></book></content></entry>"
+            + "</feed>";
+        MediaType mt = MediaType.valueOf("application/atom+xml;type=feed");
+        ByteArrayInputStream bis = new ByteArrayInputStream(feed.getBytes());
+        @SuppressWarnings({"unchecked", "rawtypes" })
+        Books books2 = (Books)provider.readFrom((Class)Books.class, Books.class, 
+                                            new Annotation[]{}, mt, null, bis);
+        List<Book> list = books2.getBooks();
+        assertEquals(2, list.size());
+        assertTrue("a".equals(list.get(0).getName()) || "a".equals(list.get(1).getName()));
+        assertTrue("b".equals(list.get(0).getName()) || "b".equals(list.get(1).getName()));
+    }
     @Test
     public void testReadEntryNoContent() throws Exception {
         /** A sample entry without content. */
"""
    retval = util.added_deleted_from_diff(string)
    for i in retval.keys():
        print(i)
        print("  " + str(retval[i].added))
        print("  " + str(retval[i].deleted))