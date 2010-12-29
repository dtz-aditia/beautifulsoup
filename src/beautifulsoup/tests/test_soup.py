# -*- coding: utf-8 -*-
"""Unit tests for Beautiful Soup.

These tests make sure the Beautiful Soup works as it should. If you
find a bug in Beautiful Soup, the best way to express it is as a test
case like this that fails."""

import re
import unittest
from beautifulsoup import *
from beautifulsoup.element import CData, Comment, Declaration, SoupStrainer, Tag
from beautifulsoup.dammit import UnicodeDammit
from beautifulsoup.builder.html5lib_builder import HTML5TreeBuilder

def additional_tests():
    return unittest.TestLoader().loadTestsFromName(__name__)


class SoupTest(unittest.TestCase):

    default_builder = HTML5TreeBuilder()

    def assertSoupEquals(self, toParse, rep=None, builder=None,
                         encoding=None):
        """Parse the given text and make sure its string rep is the other
        given text."""
        if rep == None:
            rep = toParse
        obj = BeautifulSoup(toParse, builder=self.default_builder)
        if encoding is None:
            rep2 = obj.decode()
        else:
            rep2 = obj.encode(encoding)
        self.assertEqual(rep2, rep)


class FollowThatTag(SoupTest):

    "Tests the various ways of fetching tags from a soup."

    def setUp(self):
        ml = """
        <a id="x">1</a>
        <A id="a">2</A>
        <b id="b">3</b>
        <b href="foo" id="x">4</b>
        <ac width=100>4</ac>"""
        self.soup = BeautifulStoneSoup(ml)

    def testParents(self):
        soup = BeautifulSoup('<ul id="foo"></ul><ul id="foo"><ul><ul id="foo" a="b"><b>Blah')
        b = soup.b
        self.assertEquals(len(b.findParents('ul', {'id' : 'foo'})), 2)
        self.assertEquals(b.findParent('ul')['a'], 'b')

    PROXIMITY_TEST = BeautifulSoup('<b id="1"><b id="2"><b id="3"><b id="4">')

    def testNext(self):
        soup = self.PROXIMITY_TEST
        b = soup.find('b', {'id' : 2})
        self.assertEquals(b.findNext('b')['id'], '3')
        self.assertEquals(b.findNext('b')['id'], '3')
        self.assertEquals(len(b.findAllNext('b')), 2)
        self.assertEquals(len(b.findAllNext('b', {'id' : 4})), 1)

    def testPrevious(self):
        soup = self.PROXIMITY_TEST
        b = soup.find('b', {'id' : 3})
        self.assertEquals(b.findPrevious('b')['id'], '2')
        self.assertEquals(b.findPrevious('b')['id'], '2')
        self.assertEquals(len(b.findAllPrevious('b')), 2)
        self.assertEquals(len(b.findAllPrevious('b', {'id' : 2})), 1)


    SIBLING_TEST = BeautifulSoup('<blockquote id="1"><blockquote id="1.1"></blockquote></blockquote><blockquote id="2"><blockquote id="2.1"></blockquote></blockquote><blockquote id="3"><blockquote id="3.1"></blockquote></blockquote><blockquote id="4">')

    def testNextSibling(self):
        soup = self.SIBLING_TEST
        tag = 'blockquote'
        b = soup.find(tag, {'id' : 2})
        self.assertEquals(b.findNext(tag)['id'], '2.1')
        self.assertEquals(b.findNextSibling(tag)['id'], '3')
        self.assertEquals(b.findNextSibling(tag)['id'], '3')
        self.assertEquals(len(b.findNextSiblings(tag)), 2)
        self.assertEquals(len(b.findNextSiblings(tag, {'id' : 4})), 1)

    def testPreviousSibling(self):
        soup = self.SIBLING_TEST
        tag = 'blockquote'
        b = soup.find(tag, {'id' : 3})
        self.assertEquals(b.findPrevious(tag)['id'], '2.1')
        self.assertEquals(b.findPreviousSibling(tag)['id'], '2')
        self.assertEquals(b.findPreviousSibling(tag)['id'], '2')
        self.assertEquals(len(b.findPreviousSiblings(tag)), 2)
        self.assertEquals(len(b.findPreviousSiblings(tag, id=1)), 1)

    def testTextNavigation(self):
        soup = BeautifulSoup('Foo<b>Bar</b><i id="1"><b>Baz<br />Blee<hr id="1"/></b></i>Blargh')
        baz = soup.find(text='Baz')
        self.assertEquals(baz.findParent("i")['id'], '1')
        self.assertEquals(baz.findNext(text='Blee'), 'Blee')
        self.assertEquals(baz.findNextSibling(text='Blee'), 'Blee')
        self.assertEquals(baz.findNextSibling(text='Blargh'), None)
        self.assertEquals(baz.findNextSibling('hr')['id'], '1')

class SiblingRivalry(SoupTest):
    "Tests the nextSibling and previousSibling navigation."

    def testSiblings(self):
        soup = BeautifulSoup("<ul><li>1<p>A</p>B<li>2<li>3</ul>")
        secondLI = soup.find('li').nextSibling
        self.assert_(secondLI.name == 'li' and secondLI.string == '2')
        self.assertEquals(soup.find(text='1').nextSibling.name, 'p')
        self.assertEquals(soup.find('p').nextSibling, 'B')
        self.assertEquals(soup.find('p').nextSibling.previousSibling.nextSibling, 'B')

class OnlyTheLonely(SoupTest):
    "Tests the parseOnly argument to the constructor."
    def setUp(self):
        x = []
        for i in range(1,6):
            x.append('<a id="%s">' % i)
            for j in range(100,103):
                x.append('<b id="%s.%s">Content %s.%s</b>' % (i,j, i,j))
            x.append('</a>')
        self.x = ''.join(x)

    def testOnly(self):
        strainer = SoupStrainer("b")
        soup = BeautifulSoup(self.x, parseOnlyThese=strainer)
        self.assertEquals(len(soup), 15)

        strainer = SoupStrainer(id=re.compile("100.*"))
        soup = BeautifulSoup(self.x, parseOnlyThese=strainer)
        self.assertEquals(len(soup), 5)

        strainer = SoupStrainer(text=re.compile("10[01].*"))
        soup = BeautifulSoup(self.x, parseOnlyThese=strainer)
        self.assertEquals(len(soup), 10)

        strainer = SoupStrainer(text=lambda(x):x[8]=='3')
        soup = BeautifulSoup(self.x, parseOnlyThese=strainer)
        self.assertEquals(len(soup), 3)

class PickleMeThis(SoupTest):
    "Testing features like pickle and deepcopy."

    def setUp(self):
        self.page = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"
"http://www.w3.org/TR/REC-html40/transitional.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Beautiful Soup: We called him Tortoise because he taught us.</title>
<link rev="made" href="mailto:leonardr@segfault.org">
<meta name="Description" content="Beautiful Soup: an HTML parser optimized for screen-scraping.">
<meta name="generator" content="Markov Approximation 1.4 (module: leonardr)">
<meta name="author" content="Leonard Richardson">
</head>
<body>
<a href="foo">foo</a>
<a href="foo"><b>bar</b></a>
</body>
</html>"""

        self.soup = BeautifulSoup(self.page)

    def testPickle(self):
        import pickle
        dumped = pickle.dumps(self.soup, 2)
        loaded = pickle.loads(dumped)
        self.assertEqual(loaded.__class__, BeautifulSoup)
        self.assertEqual(loaded.decode(), self.soup.decode())

    def testDeepcopy(self):
        from copy import deepcopy
        deepcopy(BeautifulSoup("<a></a>"))
        copied = deepcopy(self.soup)
        self.assertEqual(copied.decode(), self.soup.decode())

    def testUnicodePickle(self):
        import cPickle as pickle
        html = "<b>" + chr(0xc3) + "</b>"
        soup = BeautifulSoup(html)
        dumped = pickle.dumps(soup, pickle.HIGHEST_PROTOCOL)
        loaded = pickle.loads(dumped)
        self.assertEqual(loaded.decode(), soup.decode())


class WriteOnlyCode(SoupTest):
    "Testing the modification of the tree."

    def testModifyAttributes(self):
        soup = BeautifulSoup('<a id="1"></a>')
        soup.a['id'] = 2
        self.assertEqual(soup.decode(), '<a id="2"></a>')
        del(soup.a['id'])
        self.assertEqual(soup.decode(), '<a></a>')
        soup.a['id2'] = 'foo'
        self.assertEqual(soup.decode(), '<a id2="foo"></a>')

    def testNewTagCreation(self):
        "Makes sure tags don't step on each others' toes."
        soup = BeautifulSoup()
        builder = HTMLParserTreeBuilder()
        a = Tag(soup, builder, 'a')
        ol = Tag(soup, builder, 'ol')
        a['href'] = 'http://foo.com/'
        self.assertRaises(KeyError, lambda : ol['href'])

    def testTagReplacement(self):
        # Make sure you can replace an element with itself.
        text = "<a><b></b><c>Foo<d></d></c></a><a><e></e></a>"
        soup = BeautifulSoup(text)
        c = soup.c
        soup.c.replaceWith(c)
        self.assertEquals(soup.decode(), text)

        # A very simple case
        soup = BeautifulSoup("<b>Argh!</b>")
        soup.find(text="Argh!").replaceWith("Hooray!")
        newText = soup.find(text="Hooray!")
        b = soup.b
        self.assertEqual(newText.previous, b)
        self.assertEqual(newText.parent, b)
        self.assertEqual(newText.previous.next, newText)
        self.assertEqual(newText.next, None)

        # A more complex case
        soup = BeautifulSoup("<a><b>Argh!</b><c></c><d></d></a>")
        soup.b.insert(1, "Hooray!")
        newText = soup.find(text="Hooray!")
        self.assertEqual(newText.previous, "Argh!")
        self.assertEqual(newText.previous.next, newText)

        self.assertEqual(newText.previousSibling, "Argh!")
        self.assertEqual(newText.previousSibling.nextSibling, newText)

        self.assertEqual(newText.nextSibling, None)
        self.assertEqual(newText.next, soup.c)

        text = "<html>There's <b>no</b> business like <b>show</b> business</html>"
        soup = BeautifulSoup(text)
        no, show = soup.findAll('b')
        show.replaceWith(no)
        self.assertEquals(soup.decode(), "<html>There's  business like <b>no</b> business</html>")

        # Even more complex
        soup = BeautifulSoup("<a><b>Find</b><c>lady!</c><d></d></a>")
        builder = HTMLParserTreeBuilder()
        tag = Tag(soup, builder, 'magictag')
        tag.insert(0, "the")
        soup.a.insert(1, tag)

        b = soup.b
        c = soup.c
        theText = tag.find(text=True)
        findText = b.find(text="Find")

        self.assertEqual(findText.next, tag)
        self.assertEqual(tag.previous, findText)
        self.assertEqual(b.nextSibling, tag)
        self.assertEqual(tag.previousSibling, b)
        self.assertEqual(tag.nextSibling, c)
        self.assertEqual(c.previousSibling, tag)

        self.assertEqual(theText.next, c)
        self.assertEqual(c.previous, theText)

        # Aand... incredibly complex.
        soup = BeautifulSoup("""<a>We<b>reserve<c>the</c><d>right</d></b></a><e>to<f>refuse</f><g>service</g></e>""")
        f = soup.f
        a = soup.a
        c = soup.c
        e = soup.e
        weText = a.find(text="We")
        soup.b.replaceWith(soup.f)
        self.assertEqual(soup.decode(), "<a>We<f>refuse</f></a><e>to<g>service</g></e>")

        self.assertEqual(f.previous, weText)
        self.assertEqual(weText.next, f)
        self.assertEqual(f.previousSibling, weText)
        self.assertEqual(f.nextSibling, None)
        self.assertEqual(weText.nextSibling, f)

    def testAppend(self):
       doc = "<p>Don't leave me <b>here</b>.</p> <p>Don't leave me.</p>"
       soup = BeautifulSoup(doc)
       second_para = soup('p')[1]
       bold = soup.find('b')
       soup('p')[1].append(soup.find('b'))
       self.assertEqual(bold.parent, second_para)
       self.assertEqual(soup.decode(),
                        "<p>Don't leave me .</p> "
                        "<p>Don't leave me.<b>here</b></p>")

    def testTagExtraction(self):
        # A very simple case
        text = '<html><div id="nav">Nav crap</div>Real content here.</html>'
        soup = BeautifulSoup(text)
        extracted = soup.find("div", id="nav").extract()
        self.assertEqual(soup.decode(), "<html>Real content here.</html>")
        self.assertEqual(extracted.decode(), '<div id="nav">Nav crap</div>')

        # A simple case, a more complex test.
        text = "<doc><a>1<b>2</b></a><a>i<b>ii</b></a><a>A<b>B</b></a></doc>"
        soup = BeautifulStoneSoup(text)
        doc = soup.doc
        numbers, roman, letters = soup("a")

        self.assertEqual(roman.parent, doc)
        oldPrevious = roman.previous
        endOfThisTag = roman.nextSibling.previous
        self.assertEqual(oldPrevious, "2")
        self.assertEqual(roman.next, "i")
        self.assertEqual(endOfThisTag, "ii")
        self.assertEqual(roman.previousSibling, numbers)
        self.assertEqual(roman.nextSibling, letters)

        roman.extract()
        self.assertEqual(roman.parent, None)
        self.assertEqual(roman.previous, None)
        self.assertEqual(roman.next, "i")
        self.assertEqual(letters.previous, '2')
        self.assertEqual(roman.previousSibling, None)
        self.assertEqual(roman.nextSibling, None)
        self.assertEqual(endOfThisTag.next, None)
        self.assertEqual(roman.b.contents[0].next, None)
        self.assertEqual(numbers.nextSibling, letters)
        self.assertEqual(letters.previousSibling, numbers)
        self.assertEqual(len(doc.contents), 2)
        self.assertEqual(doc.contents[0], numbers)
        self.assertEqual(doc.contents[1], letters)

        # A more complex case.
        text = "<a>1<b>2<c>Hollywood, baby!</c></b></a>3"
        soup = BeautifulStoneSoup(text)
        one = soup.find(text="1")
        three = soup.find(text="3")
        toExtract = soup.b
        soup.b.extract()
        self.assertEqual(one.next, three)
        self.assertEqual(three.previous, one)
        self.assertEqual(one.parent.nextSibling, three)
        self.assertEqual(three.previousSibling, soup.a)

class YoureSoLiteral(SoupTest):
    "Test literal mode."
    def testLiteralMode(self):
        text = "<script>if (i<imgs.length)</script><b>Foo</b>"
        soup = BeautifulSoup(text)
        self.assertEqual(soup.script.contents[0], "if (i<imgs.length)")
        self.assertEqual(soup.b.contents[0], "Foo")

    def testTextArea(self):
        text = "<textarea><b>This is an example of an HTML tag</b><&<&</textarea>"
        soup = BeautifulSoup(text)
        self.assertEqual(soup.textarea.contents[0],
                         "<b>This is an example of an HTML tag</b><&<&")

class NestableEgg(SoupTest):
    """Here we test tag nesting. TEST THE NEST, DUDE! X-TREME!"""

    def testNestedTables(self):
        text = """<table id="1"><tr><td>Here's another table:
        <table id="2"><tr><td>Juicy text</td></tr></table></td></tr></table>"""
        soup = BeautifulSoup(text)
        self.assertEquals(soup.table.table.td.string, 'Juicy text')
        self.assertEquals(len(soup.findAll('table')), 2)
        self.assertEquals(len(soup.table.findAll('table')), 1)
        self.assertEquals(soup.find('table', {'id' : 2}).parent.parent.parent.name,
                          'table')

        text = "<table><tr><td><div><table>Foo</table></div></td></tr></table>"
        soup = BeautifulSoup(text)
        self.assertEquals(soup.table.tr.td.div.table.contents[0], "Foo")

        text = """<table><thead><tr>Foo</tr></thead><tbody><tr>Bar</tr></tbody>
        <tfoot><tr>Baz</tr></tfoot></table>"""
        soup = BeautifulSoup(text)
        self.assertEquals(soup.table.thead.tr.contents[0], "Foo")

    def testBadNestedTables(self):
        soup = BeautifulSoup("<table><tr><table><tr id='nested'>")
        self.assertEquals(soup.table.tr.table.tr['id'], 'nested')

class CleanupOnAisleFour(SoupTest):
    """Here we test cleanup of text that breaks HTMLParser or is just
    obnoxious."""

    def testCData(self):
        xml = "<root>foo<![CDATA[foobar]]>bar</root>"
        self.assertSoupEquals(xml, xml)
        r = re.compile("foo.*bar")
        soup = BeautifulSoup(xml)
        self.assertEquals(soup.find(text=r).string, "foobar")
        self.assertEquals(soup.find(text=r).__class__, CData)

    def testComments(self):
        xml = "foo<!--foobar-->baz"
        self.assertSoupEquals(xml)
        r = re.compile("foo.*bar")
        soup = BeautifulSoup(xml)
        self.assertEquals(soup.find(text=r).string, "foobar")
        self.assertEquals(soup.find(text="foobar").__class__, Comment)

    def testDeclaration(self):
        xml = "foo<!DOCTYPE foobar>baz"
        self.assertSoupEquals(xml)
        r = re.compile(".*foo.*bar")
        soup = BeautifulSoup(xml)
        text = "DOCTYPE foobar"
        self.assertEquals(soup.find(text=r).string, text)
        self.assertEquals(soup.find(text=text).__class__, Declaration)

        namespaced_doctype = ('<!DOCTYPE xsl:stylesheet SYSTEM "htmlent.dtd">'
                              '<html>foo</html>')
        soup = BeautifulSoup(namespaced_doctype)
        self.assertEquals(soup.contents[0],
                          'DOCTYPE xsl:stylesheet SYSTEM "htmlent.dtd"')
        self.assertEquals(soup.html.contents[0], 'foo')

    def testEntityConversions(self):
        text = "&lt;&lt;sacr&eacute;&#32;bleu!&gt;&gt;"
        soup = BeautifulStoneSoup(text)
        self.assertSoupEquals(text)

        xmlEnt = Entities.XML_ENTITIES
        htmlEnt = Entities.HTML_ENTITIES
        xhtmlEnt = Entities.XHTML_ENTITIES

        xmlBuilder = HTMLParserXMLTreeBuilder(convertEntities=xmlEnt)
        htmlBuilder = HTMLParserXMLTreeBuilder(convertEntities=htmlEnt)
        xhtmlBuilder = HTMLParserXMLTreeBuilder(convertEntities=xhtmlEnt)

        soup = BeautifulStoneSoup(text, xmlBuilder)
        self.assertEquals(soup.decode(), "<<sacr&eacute; bleu!>>")

        soup = BeautifulStoneSoup(text, xmlBuilder)
        self.assertEquals(soup.decode(), "<<sacr&eacute; bleu!>>")

        soup = BeautifulStoneSoup(text, htmlBuilder)
        self.assertEquals(soup.decode(), u"<<sacr\xe9 bleu!>>")

        # Make sure the "XML", "HTML", and "XHTML" settings work.
        text = "&lt;&trade;&apos;"
        soup = BeautifulStoneSoup(text, xmlBuilder)
        self.assertEquals(soup.decode(), u"<&trade;'")

        soup = BeautifulStoneSoup(text, htmlBuilder)
        self.assertEquals(soup.decode(), u"<\u2122&apos;")

        soup = BeautifulStoneSoup(text, xhtmlBuilder)
        self.assertEquals(soup.decode(), u"<\u2122'")

    def testNonBreakingSpaces(self):
        builder = HTMLParserTreeBuilder(
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        soup = BeautifulSoup("<a>&nbsp;&nbsp;</a>", builder)
        self.assertEquals(soup.decode(), u"<a>\xa0\xa0</a>")

    def testWhitespaceInDeclaration(self):
        self.assertSoupEquals('<! DOCTYPE>', '<!DOCTYPE>')

    def testJunkInDeclaration(self):
        self.assertSoupEquals('<! Foo = -8>a', '<!Foo = -8>a')

    def testIncompleteDeclaration(self):
        self.assertSoupEquals('a<!b <p>c')

    def testEntityReplacement(self):
        self.assertSoupEquals('<b>hello&nbsp;there</b>')

    def testEntitiesInAttributeValues(self):
        self.assertSoupEquals('<x t="x&#241;">', '<x t="x\xc3\xb1"></x>',
                              encoding='utf-8')
        self.assertSoupEquals('<x t="x&#xf1;">', '<x t="x\xc3\xb1"></x>',
                              encoding='utf-8')

        builder = HTMLParserTreeBuilder(convertEntities=Entities.HTML_ENTITIES)
        soup = BeautifulSoup('<x t="&gt;&trade;">', builder)
        self.assertEquals(soup.decode(), u'<x t="&gt;\u2122"></x>')

        uri = "http://crummy.com?sacr&eacute;&amp;bleu"
        link = '<a href="%s"></a>' % uri

        soup = BeautifulSoup(link, builder)
        self.assertEquals(soup.decode(),
                          link.replace("&eacute;", u"\xe9"))

        uri = "http://crummy.com?sacr&eacute;&bleu"
        link = '<a href="%s"></a>' % uri
        soup = BeautifulSoup(link, builder)
        self.assertEquals(soup.a['href'],
                          uri.replace("&eacute;", u"\xe9"))

    def testNakedAmpersands(self):
        builder = HTMLParserXMLTreeBuilder(convertEntities=Entities.HTML_ENTITIES)
        soup = BeautifulStoneSoup("AT&T ", builder)
        self.assertEquals(soup.decode(), 'AT&amp;T ')

        nakedAmpersandInASentence = "AT&T was Ma Bell"
        soup = BeautifulStoneSoup(nakedAmpersandInASentence, builder)
        self.assertEquals(soup.decode(), \
               nakedAmpersandInASentence.replace('&','&amp;'))

        invalidURL = '<a href="http://example.org?a=1&b=2;3">foo</a>'
        validURL = invalidURL.replace('&','&amp;')
        soup = BeautifulStoneSoup(invalidURL)
        self.assertEquals(soup.decode(), validURL)

        soup = BeautifulStoneSoup(validURL)
        self.assertEquals(soup.decode(), validURL)


class EncodeRed(SoupTest):
    """Tests encoding conversion, Unicode conversion, and Microsoft
    smart quote fixes."""

    def testUnicodeDammitStandalone(self):
        markup = "<foo>\x92</foo>"
        dammit = UnicodeDammit(markup)
        self.assertEquals(dammit.unicode, "<foo>&#x2019;</foo>")

        hebrew = "\xed\xe5\xec\xf9"
        dammit = UnicodeDammit(hebrew, ["iso-8859-8"])
        self.assertEquals(dammit.unicode, u'\u05dd\u05d5\u05dc\u05e9')
        self.assertEquals(dammit.originalEncoding, 'iso-8859-8')

    def testGarbageInGarbageOut(self):
        ascii = "<foo>a</foo>"
        asciiSoup = BeautifulStoneSoup(ascii)
        self.assertEquals(ascii, asciiSoup.decode())

        unicodeData = u"<foo>\u00FC</foo>"
        utf8 = unicodeData.encode("utf-8")
        self.assertEquals(utf8, '<foo>\xc3\xbc</foo>')

        unicodeSoup = BeautifulStoneSoup(unicodeData)
        self.assertEquals(unicodeData, unicodeSoup.decode())
        self.assertEquals(unicodeSoup.foo.string, u'\u00FC')

        utf8Soup = BeautifulStoneSoup(utf8, fromEncoding='utf-8')
        self.assertEquals(utf8, utf8Soup.encode('utf-8'))
        self.assertEquals(utf8Soup.originalEncoding, "utf-8")

        utf8Soup = BeautifulStoneSoup(unicodeData)
        self.assertEquals(utf8, utf8Soup.encode('utf-8'))
        self.assertEquals(utf8Soup.originalEncoding, None)


    def testHandleInvalidCodec(self):
        for bad_encoding in ['.utf8', '...', 'utF---16.!']:
            soup = BeautifulSoup(u"Räksmörgås".encode("utf-8"),
                                 fromEncoding=bad_encoding)
            self.assertEquals(soup.originalEncoding, 'utf-8')

    def testUnicodeSearch(self):
        html = u'<html><body><h1>Räksmörgås</h1></body></html>'
        soup = BeautifulSoup(html)
        self.assertEqual(soup.find(text=u'Räksmörgås'),u'Räksmörgås')

    def testRewrittenXMLHeader(self):
        euc_jp = '<?xml version="1.0 encoding="euc-jp"?>\n<foo>\n\xa4\xb3\xa4\xec\xa4\xcfEUC-JP\xa4\xc7\xa5\xb3\xa1\xbc\xa5\xc7\xa5\xa3\xa5\xf3\xa5\xb0\xa4\xb5\xa4\xec\xa4\xbf\xc6\xfc\xcb\xdc\xb8\xec\xa4\xce\xa5\xd5\xa5\xa1\xa5\xa4\xa5\xeb\xa4\xc7\xa4\xb9\xa1\xa3\n</foo>\n'
        utf8 = "<?xml version='1.0' encoding='utf-8'?>\n<foo>\n\xe3\x81\x93\xe3\x82\x8c\xe3\x81\xafEUC-JP\xe3\x81\xa7\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x87\xe3\x82\xa3\xe3\x83\xb3\xe3\x82\xb0\xe3\x81\x95\xe3\x82\x8c\xe3\x81\x9f\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e\xe3\x81\xae\xe3\x83\x95\xe3\x82\xa1\xe3\x82\xa4\xe3\x83\xab\xe3\x81\xa7\xe3\x81\x99\xe3\x80\x82\n</foo>\n"
        soup = BeautifulStoneSoup(euc_jp)
        if soup.originalEncoding != "euc-jp":
            raise Exception("Test failed when parsing euc-jp document. "
                            "If you're running Python >=2.4, or you have "
                            "cjkcodecs installed, this is a real problem. "
                            "Otherwise, ignore it.")

        self.assertEquals(soup.originalEncoding, "euc-jp")
        self.assertEquals(soup.encodeContents('utf-8'), utf8)

        old_text = "<?xml encoding='windows-1252'><foo>\x92</foo>"
        new_text = "<?xml version='1.0' encoding='utf-8'?><foo>&rsquo;</foo>"
        self.assertSoupEquals(old_text, new_text)

    def testRewrittenMetaTag(self):
        no_shift_jis_html = '''<html><head>\n<meta http-equiv="Content-language" content="ja" /></head><body><pre>\n\x82\xb1\x82\xea\x82\xcdShift-JIS\x82\xc5\x83R\x81[\x83f\x83B\x83\x93\x83O\x82\xb3\x82\xea\x82\xbd\x93\xfa\x96{\x8c\xea\x82\xcc\x83t\x83@\x83C\x83\x8b\x82\xc5\x82\xb7\x81B\n</pre></body></html>'''
        soup = BeautifulSoup(no_shift_jis_html)

        # Beautiful Soup used to try to rewrite the meta tag even if the
        # meta tag got filtered out by the strainer. This test makes
        # sure that doesn't happen.
        strainer = SoupStrainer('pre')
        soup = BeautifulSoup(no_shift_jis_html, parseOnlyThese=strainer)
        self.assertEquals(soup.contents[0].name, 'pre')

        meta_tag = ('<meta content="text/html; charset=x-sjis" '
                    'http-equiv="Content-type" />')
        shift_jis_html = (
            '<html><head>\n%s\n'
            '<meta http-equiv="Content-language" content="ja" />'
            '</head><body><pre>\n'
            '\x82\xb1\x82\xea\x82\xcdShift-JIS\x82\xc5\x83R\x81[\x83f'
            '\x83B\x83\x93\x83O\x82\xb3\x82\xea\x82\xbd\x93\xfa\x96{\x8c'
            '\xea\x82\xcc\x83t\x83@\x83C\x83\x8b\x82\xc5\x82\xb7\x81B\n'
            '</pre></body></html>') % meta_tag
        soup = BeautifulSoup(shift_jis_html)
        if soup.originalEncoding != "shift-jis":
            raise Exception("Test failed when parsing shift-jis document "
                            "with meta tag '%s'."
                            "If you're running Python >=2.4, or you have "
                            "cjkcodecs installed, this is a real problem. "
                            "Otherwise, ignore it." % meta_tag)
        self.assertEquals(soup.originalEncoding, "shift-jis")

        content_type_tag = soup.meta['content']
        self.assertEquals(content_type_tag[content_type_tag.find('charset='):],
                          'charset=%SOUP-ENCODING%')
        content_type = str(soup.meta)
        index = content_type.find('charset=')
        self.assertEqual(content_type[index:index+len('charset=utf8')+1],
                         'charset=utf-8')
        content_type = soup.meta.encode('shift-jis')
        index = content_type.find('charset=')
        self.assertEqual(content_type[index:index+len('charset=shift-jis')],
                         'charset=shift-jis'.encode())

        self.assertEquals(soup.encode('utf-8'), (
                '<html><head>\n'
                '<meta content="text/html; charset=utf-8" '
                'http-equiv="Content-type" />\n'
                '<meta http-equiv="Content-language" content="ja" />'
                '</head><body><pre>\n'
                '\xe3\x81\x93\xe3\x82\x8c\xe3\x81\xafShift-JIS\xe3\x81\xa7\xe3'
                '\x82\xb3\xe3\x83\xbc\xe3\x83\x87\xe3\x82\xa3\xe3\x83\xb3\xe3'
                '\x82\xb0\xe3\x81\x95\xe3\x82\x8c\xe3\x81\x9f\xe6\x97\xa5\xe6'
                '\x9c\xac\xe8\xaa\x9e\xe3\x81\xae\xe3\x83\x95\xe3\x82\xa1\xe3'
                '\x82\xa4\xe3\x83\xab\xe3\x81\xa7\xe3\x81\x99\xe3\x80\x82\n'
                '</pre></body></html>'))
        self.assertEquals(soup.encode("shift-jis"),
                          shift_jis_html.replace('x-sjis'.encode(),
                                                 'shift-jis'.encode()))

        isolatin = """<html><meta http-equiv="Content-type" content="text/html; charset=ISO-Latin-1" />Sacr\xe9 bleu!</html>"""
        soup = BeautifulSoup(isolatin)

        utf8 = isolatin.replace("ISO-Latin-1".encode(), "utf-8".encode())
        utf8 = utf8.replace("\xe9", "\xc3\xa9")
        self.assertSoupEquals(soup.encode("utf-8"), utf8, encoding='utf-8')

    def testHebrew(self):
        iso_8859_8= '<HEAD>\n<TITLE>Hebrew (ISO 8859-8) in Visual Directionality</TITLE>\n\n\n\n</HEAD>\n<BODY>\n<H1>Hebrew (ISO 8859-8) in Visual Directionality</H1>\n\xed\xe5\xec\xf9\n</BODY>\n'
        utf8 = '<head>\n<title>Hebrew (ISO 8859-8) in Visual Directionality</title>\n</head>\n<body>\n<h1>Hebrew (ISO 8859-8) in Visual Directionality</h1>\n\xd7\x9d\xd7\x95\xd7\x9c\xd7\xa9\n</body>\n'
        soup = BeautifulStoneSoup(iso_8859_8, fromEncoding="iso-8859-8")
        self.assertEquals(soup.encode('utf-8'), utf8)

    def testSmartQuotesNotSoSmartAnymore(self):
        self.assertSoupEquals("\x91Foo\x92 <!--blah-->",
                              '&lsquo;Foo&rsquo; <!--blah-->')

    def testDontConvertSmartQuotesWhenAlsoConvertingEntities(self):
        smartQuotes = "Il a dit, \x8BSacr&eacute; bl&#101;u!\x9b"
        soup = BeautifulSoup(smartQuotes)
        self.assertEquals(soup.decode(),
                          'Il a dit, &lsaquo;Sacr&eacute; bl&#101;u!&rsaquo;')
        builder = HTMLParserTreeBuilder(convertEntities="html")
        soup = BeautifulSoup(smartQuotes, builder)
        self.assertEquals(soup.encode('utf-8'),
                          'Il a dit, \xe2\x80\xb9Sacr\xc3\xa9 bleu!\xe2\x80\xba')

    def testDontSeeSmartQuotesWhereThereAreNone(self):
        utf_8 = "\343\202\261\343\203\274\343\202\277\343\202\244 Watch"
        self.assertSoupEquals(utf_8, encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
