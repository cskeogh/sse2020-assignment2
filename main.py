import git
import os
import os.path
import re
import util
import datetime
import pprint

remote_link = "https://github.com/apache/cxf.git"
local_link = "repo/cxf"
# the_fixing_commit = "9deb2d179758d3da47ce3ea492c2606c0a6a8475"
the_fixing_commit = "7d30aec26dc"
# affected_files = \
#     ["rt/rs/extensions/providers/src/main/java/org/apache/cxf/jaxrs/provider/atom/AbstractAtomProvider.java",
#      "rt/rs/extensions/providers/src/test/java/org/apache/cxf/jaxrs/provider/atom/AtomPojoProviderTest.java"]

class Progress(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(self._cur_line)


def assignment2():
    if os.path.isdir(local_link):
        print(local_link + " already exists. Skipping git clone")
    else:
        git.Repo.clone_from(remote_link, local_link, progress=Progress())
    repo = git.Repo(local_link)
    added_deleted = find_added_deleted_lines(repo, the_fixing_commit)
    deleted_commits = assignment2_part3a(repo, the_fixing_commit, added_deleted)
    added_commits = assignment2_part3b(repo, the_fixing_commit, added_deleted)
    vcc = assignment2_part3c(deleted_commits, added_commits)

    # added_deleted = find_added_deleted_lines(repo, vcc)
    # deleted_commits = assignment2_part3a(repo, vcc, added_deleted)
    # added_commits = assignment2_part3b(repo, vcc, added_deleted)
    # vcc = assignment2_part3c(deleted_commits, added_commits)


    # assignment2_part5a(repo, vcc)
    # assignment2_part5b(repo, vcc)
    # assignment2_part5c(repo, vcc)
    # totals = assignment2_part5de(repo, vcc)
    # assignment2_part5fg(repo, vcc, totals)
    # assignment2_part5h(repo, vcc)
    # assignment2_part5i(repo, vcc)
    # all_authors = assignment2_part5j(repo, vcc)
    # assignment2_part5k(repo, vcc, all_authors)

def find_added_deleted_lines(repo, fixing_commit):
    show_data = git_output = repo.git.show(fixing_commit, '--format=format:')
    return util.added_deleted_from_diff(show_data)

def assignment2_part3a(repo, fixing_commit, added_deleted):
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
    print("\nPart 3.b -- lines added, smallest enclosing scope ---------------------")
    frequently_identified_commit = {}
    test_decorator_re = re.compile(r"^\s*@Test\s*$")

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
    print("\nPart 3.c -- frequently identified commit as the VCC ---------------------")
    frequently_identified_commits = util.merge_two_dicts(deleted_commits, added_commits)

    vcc = max(frequently_identified_commits, key=frequently_identified_commits.get)
    print(vcc + ' (identified in ' + str(frequently_identified_commits[vcc]) + ' rows)')
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
    assignment2()
    string = """/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.cxf.jaxrs.provider.atom;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.StringReader;
import java.lang.annotation.Annotation;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import javax.ws.rs.core.MediaType;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlRootElement;

import org.apache.abdera.model.Entry;
import org.apache.abdera.model.Feed;
import org.apache.cxf.jaxrs.impl.MetadataMap;
import org.apache.cxf.jaxrs.provider.JAXBElementProvider;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import org.springframework.context.support.ClassPathXmlApplicationContext;

public class AtomPojoProviderTest extends Assert {

    private ClassPathXmlApplicationContext ctx;
    
    @Before
    public void setUp() {
        ctx = 
            new ClassPathXmlApplicationContext(
                new String[] {"/org/apache/cxf/jaxrs/provider/atom/servers.xml"});
    }
    
    @Test
    public void testWriteFeedWithBuilders() throws Exception {
        AtomPojoProvider provider = (AtomPojoProvider)ctx.getBean("atom");
        assertNotNull(provider);
        provider.setFormattedOutput(true);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        
        Books books = new Books();
        List<Book> bs = new ArrayList<Book>();
        bs.add(new Book("a"));
        bs.add(new Book("b"));
        books.setBooks(bs);
        provider.writeTo(books, Books.class, Books.class, new Annotation[]{},
                         MediaType.valueOf("application/atom+xml"), null, bos);
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        Feed feed = new AtomFeedProvider().readFrom(Feed.class, null, null, null, null, bis);
        assertEquals("Books", feed.getTitle()); 
        List<Entry> entries = feed.getEntries();
        assertEquals(2, entries.size());
        verifyEntry(getEntry(entries, "a"), "a");
        verifyEntry(getEntry(entries, "b"), "b");
    }
    
    @Test
    public void testWriteFeedWithBuildersNoJaxb() throws Exception {
        AtomPojoProvider provider = (AtomPojoProvider)ctx.getBean("atomNoJaxb");
        assertNotNull(provider);
        provider.setFormattedOutput(true);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        
        Books books = new Books();
        List<Book> bs = new ArrayList<Book>();
        bs.add(new Book("a"));
        bs.add(new Book("b"));
        books.setBooks(bs);
        provider.writeTo(books, Books.class, Books.class, new Annotation[]{},
                         MediaType.valueOf("application/atom+xml"), null, bos);
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        Feed feed = new AtomFeedProvider().readFrom(Feed.class, null, null, null, null, bis);
        assertEquals("Books", feed.getTitle()); 
        List<Entry> entries = feed.getEntries();
        assertEquals(2, entries.size());
        
        Entry entryA = getEntry(entries, "a");
        verifyEntry(entryA, "a");
        String entryAContent = entryA.getContent();
        assertTrue("<a/>".equals(entryAContent) || "<a><a/>".equals(entryAContent)
                   || "<a xmlns=\"\"/>".equals(entryAContent));
        
        Entry entryB = getEntry(entries, "b");
        verifyEntry(entryB, "b");
        String entryBContent = entryB.getContent();
        assertTrue("<b/>".equals(entryBContent) || "<b><b/>".equals(entryBContent)
                   || "<b xmlns=\"\"/>".equals(entryBContent));
    }
    
    @Test
    public void testWriteEntryWithBuilders() throws Exception {
        AtomPojoProvider provider = (AtomPojoProvider)ctx.getBean("atom2");
        assertNotNull(provider);
        provider.setFormattedOutput(true);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        provider.writeTo(new Book("a"), Book.class, Book.class, new Annotation[]{},
                         MediaType.valueOf("application/atom+xml;type=entry"), null, bos);
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        Entry entry = new AtomEntryProvider().readFrom(Entry.class, null, null, null, null, bis);
        verifyEntry(entry, "a");
        
    }
    
    @Test
    public void testReadEntryWithBuilders() throws Exception {
        AtomPojoProvider provider = (AtomPojoProvider)ctx.getBean("atom3");
        assertNotNull(provider);
        doTestReadEntry(provider);
    }
    
    @Test
    public void testReadEntryWithoutBuilders() throws Exception {
        doTestReadEntry(new AtomPojoProvider());
    }
    
    private void doTestReadEntry(AtomPojoProvider provider) throws Exception {
        provider.setFormattedOutput(true);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        MediaType mt = MediaType.valueOf("application/atom+xml;type=entry");
        provider.writeTo(new Book("a"), Book.class, Book.class, new Annotation[]{}, mt, null, bos);
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        @SuppressWarnings({"unchecked", "rawtypes" })
        Book book = (Book)provider.readFrom((Class)Book.class, Book.class, 
                                            new Annotation[]{}, mt, null, bis);
        assertEquals("a", book.getName());
    }
    @Test
    public void testReadEntryNoBuilders2() throws Exception {
        final String entry = 
            "<!DOCTYPE entry SYSTEM \"entry://entry\"><entry xmlns=\"http://www.w3.org/2005/Atom\">"
            + "<title type=\"text\">a</title>"
            + "<content type=\"application/xml\">"
            + "<book xmlns=\"\">"
            + "<name>a</name>"
            + "</book>"
            + "</content>"
            + "</entry>";
        AtomPojoProvider provider = new AtomPojoProvider();
        ByteArrayInputStream bis = new ByteArrayInputStream(entry.getBytes());
        MediaType mt = MediaType.valueOf("application/atom+xml;type=entry");
        @SuppressWarnings({"unchecked", "rawtypes" })
        Book book = (Book)provider.readFrom((Class)Book.class, Book.class, 
                                            new Annotation[]{}, mt, null, bis);
        assertEquals("a", book.getName());
    }
    
    
    @Test
    public void testReadFeedWithBuilders() throws Exception {
        AtomPojoProvider provider = (AtomPojoProvider)ctx.getBean("atom4");
        assertNotNull(provider);
        doTestReadFeed(provider);
    }
    
    @Test
    public void testReadFeedWithoutBuilders() throws Exception {
        AtomPojoProvider provider = new AtomPojoProvider();
        doTestReadFeed(provider);
    }

    private void doTestReadFeed(AtomPojoProvider provider) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        MediaType mt = MediaType.valueOf("application/atom+xml;type=feed");
        Books books = new Books();
        List<Book> bs = new ArrayList<Book>();
        bs.add(new Book("a"));
        bs.add(new Book("b"));
        books.setBooks(bs);
        provider.writeTo(books, Books.class, Books.class, new Annotation[]{}, mt, null, bos);
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        @SuppressWarnings({"unchecked", "rawtypes" })
        Books books2 = (Books)provider.readFrom((Class)Books.class, Books.class, 
                                            new Annotation[]{}, mt, null, bis);
        List<Book> list = books2.getBooks();
        assertEquals(2, list.size());
        assertTrue("a".equals(list.get(0).getName()) || "a".equals(list.get(1).getName()));
        assertTrue("b".equals(list.get(0).getName()) || "b".equals(list.get(1).getName()));        
    }
     
    @Test
    public void testReadFeedWithoutBuilders2() throws Exception {
        AtomPojoProvider provider = new AtomPojoProvider();
        final String feed = 
            "<!DOCTYPE feed SYSTEM \"feed://feed\"><feed xmlns=\"http://www.w3.org/2005/Atom\">"
            + "<entry><content type=\"application/xml\"><book xmlns=\"\"><name>a</name></book></content></entry>"
            + "<entry><content type=\"application/xml\"><book xmlns=\"\"><name>b</name></book></content></entry>"
            + "</feed>";
        MediaType mt = MediaType.valueOf("application/atom+xml;type=feed");
        ByteArrayInputStream bis = new ByteArrayInputStream(feed.getBytes());
        @SuppressWarnings({"unchecked", "rawtypes" })
        Books books2 = (Books)provider.readFrom((Class)Books.class, Books.class, 
                                            new Annotation[]{}, mt, null, bis);
        List<Book> list = books2.getBooks();
        assertEquals(2, list.size());
        assertTrue("a".equals(list.get(0).getName()) || "a".equals(list.get(1).getName()));
        assertTrue("b".equals(list.get(0).getName()) || "b".equals(list.get(1).getName()));
    }
    @Test
    public void testReadEntryNoContent() throws Exception {
        /** A sample entry without content. */
        final String entryNoContent =
            "<?xml version='1.0' encoding='UTF-8'?>\n" 
            + "<entry xmlns=\"http://www.w3.org/2005/Atom\">\n" 
            + "  <id>84297856</id>\n" 
            + "</entry>";

        AtomPojoProvider atomPojoProvider = new AtomPojoProvider();
        @SuppressWarnings({
            "rawtypes", "unchecked"
        })
        JaxbDataType type = (JaxbDataType)atomPojoProvider.readFrom((Class)JaxbDataType.class,
                                  JaxbDataType.class,
                                  new Annotation[0],
                                  MediaType.valueOf("application/atom+xml;type=entry"),
                                  new MetadataMap<String, String>(),
                                  new ByteArrayInputStream(entryNoContent.getBytes(StandardCharsets.UTF_8)));
        assertNull(type);
    }
    
    @Test
    public void testReadEntryWithUpperCaseTypeParam() throws Exception {
        doReadEntryWithContent("application/atom+xml;type=ENTRY");
    }
    
    @Test
    public void testReadEntryNoTypeParam() throws Exception {
        doReadEntryWithContent("application/atom+xml");
    }
    
    private void doReadEntryWithContent(String mediaType) throws Exception {
        final String entryWithContent =
            "<?xml version='1.0' encoding='UTF-8'?>\n" 
            + "<entry xmlns=\"http://www.w3.org/2005/Atom\">\n" 
            + "  <id>84297856</id>\n" 
            + "  <content type=\"application/xml\">\n" 
            + "    <jaxbDataType xmlns=\"\">\n" 
            + "    </jaxbDataType>\n" 
            + "  </content>\n" 
            + "</entry>";

        AtomPojoProvider atomPojoProvider = new AtomPojoProvider();
        @SuppressWarnings({
            "rawtypes", "unchecked"
        })
        JaxbDataType type = (JaxbDataType)atomPojoProvider.readFrom((Class)JaxbDataType.class,
                                  JaxbDataType.class,
                                  new Annotation[0],
                                  MediaType.valueOf(mediaType),
                                  new MetadataMap<String, String>(),
                                  new ByteArrayInputStream(entryWithContent.getBytes(StandardCharsets.UTF_8)));
        assertNotNull(type);
    }
    
    /**
     * A sample JAXB data-type to read data into.
     */
    @XmlRootElement
    public static class JaxbDataType {
        // no data
    }
    
    private Entry getEntry(List<Entry> entries, String title) {
        for (Entry e : entries) {
            if (title.equals(e.getTitle())) {
                return e;
            }
        }
        return null;
    }
    
    private void verifyEntry(Entry e, String title) {
        assertNotNull(e);
        assertEquals(title, e.getTitle());
    }
    
    public static class CustomFeedWriter implements AtomElementWriter<Feed, Books> {

        public void writeTo(Feed feed, Books pojoFeed) {
            feed.setTitle("Books");
        }
        
    }
    
    public static class CustomEntryWriter implements AtomElementWriter<Entry, Book> {

        public void writeTo(Entry entry, Book pojoEntry) {
            entry.setTitle(pojoEntry.getName());
        }
        
    }
    
    public static class CustomEntryReader implements AtomElementReader<Entry, Book> {

        public Book readFrom(Entry element) {
            try {
                String s = element.getContent();
                                
                Unmarshaller um = 
                    new JAXBElementProvider<Book>().getJAXBContext(Book.class, Book.class)
                        .createUnmarshaller();
                return (Book)um.unmarshal(new StringReader(s));
            } catch (Exception ex) {
                // ignore
            }
            return null;
        }
        
    }
    
    public static class CustomFeedReader implements AtomElementReader<Feed, Books> {

        public Books readFrom(Feed element) {
            Books books = new Books();
            List<Book> list = new ArrayList<Book>();
            CustomEntryReader entryReader = new CustomEntryReader();
            for (Entry e : element.getEntries()) {
                list.add(entryReader.readFrom(e));
            }
            books.setBooks(list);
            return books;
        }
        
    }
    
    public static class CustomFeedBuilder extends AbstractFeedBuilder<Books> {
        @Override
        public String getBaseUri(Books books) {
            return "http://books";
        }
    }
    
    public static class CustomEntryBuilder extends AbstractEntryBuilder<Book> {
        @Override
        public String getBaseUri(Book books) {
            return "http://book";
        }
    }
    
        
    @XmlRootElement
    public static class Book {
        private String name = "Book";

        public Book() {
            
        }
        
        public Book(String name) {
            this.name = name;
        }
        
        public void setName(String name) {
            this.name = name;
        }

        public String getName() {
            return name;
        }
        
        public String getXMLContent() {
            return "<" + name + "/>";
        }
        
    }
    
    @XmlRootElement
    public static class Books {
        
        private List<Book> books;
        
        public Books() {
            
        }
        
        public List<Book> getBooks() {
            return books;
        }
        
        public void setBooks(List<Book> list) {
            books = list;
        }
    }
}
"""
    # util.smallest_enclosing_scope(string, 148)
