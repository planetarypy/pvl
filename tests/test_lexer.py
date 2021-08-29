#!/usr/bin/env python
"""This module has new tests for the pvl decoder functions."""

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from pvl.grammar import PVLGrammar, OmniGrammar
from pvl.exceptions import LexerError

import pvl.lexer as Lexer


class TestInternal(unittest.TestCase):
    def test_prev_char(self):
        self.assertIsNone(Lexer._prev_char("foo", 0))
        self.assertEqual("f", Lexer._prev_char("foo", 1))

    def test_next_char(self):
        self.assertIsNone(Lexer._next_char("foo", 2))
        self.assertEqual("b", Lexer._next_char("fob", 1))

    def test_prepare_comment_tuples(self):
        d = dict(
            single_comments=dict(),
            multi_comments=(("/*", "*/"),),
            multi_chars=set("/*"),
            chars=set("/*"),
        )
        self.assertEqual(d, Lexer._prepare_comment_tuples((("/*", "*/"),)))

        d = dict(
            single_comments={"#": "\n"},
            multi_comments=(("/*", "*/"),),
            multi_chars=set("/*"),
            chars=set("/*#"),
        )
        self.assertEqual(
            d, Lexer._prepare_comment_tuples((("/*", "*/"), ("#", "\n")))
        )


class TestLexComments(unittest.TestCase):
    def test_lex_multichar_comments(self):
        pfn = dict(state=Lexer.Preserve.FALSE, end=None)
        pcom = dict(state=Lexer.Preserve.COMMENT, end="*/")
        self.assertEqual(
            ("", pfn), Lexer.lex_multichar_comments("a", "b", "c", "", pfn)
        )
        self.assertEqual(
            ("", pfn), Lexer.lex_multichar_comments("/", "*", "c", "", pfn)
        )
        self.assertEqual(
            ("", pfn), Lexer.lex_multichar_comments("/", "b", "*", "", pfn)
        )
        self.assertEqual(
            ("/", pfn), Lexer.lex_multichar_comments("/", "b", "c", "", pfn)
        )
        self.assertEqual(
            ("*", pcom), Lexer.lex_multichar_comments("*", "b", "c", "", pcom)
        )
        self.assertEqual(
            ("/*", pcom), Lexer.lex_multichar_comments("*", "/", "c", "", pfn)
        )
        self.assertEqual(
            ("*/", pfn), Lexer.lex_multichar_comments("*", "c", "/", "", pcom)
        )

        self.assertRaises(
            ValueError,
            Lexer.lex_multichar_comments,
            "a",
            "b",
            "c",
            "",
            pfn,
            tuple(),
        )
        self.assertRaises(
            NotImplementedError,
            Lexer.lex_multichar_comments,
            "a",
            "b",
            "c",
            "",
            pfn,
            (("/*", "*/"), ("|*", "*|")),
        )

    def test_lex_singlechar_comments(self):
        pfn = dict(state=Lexer.Preserve.FALSE, end=None)
        phash = dict(state=Lexer.Preserve.COMMENT, end="\n")
        self.assertEqual(
            ("", pfn), Lexer.lex_singlechar_comments("a", "", pfn, {"k": "v"})
        )
        self.assertEqual(
            ("#", phash),
            Lexer.lex_singlechar_comments("#", "", pfn, {"#": "\n"}),
        )
        self.assertEqual(
            ("#\n", pfn),
            Lexer.lex_singlechar_comments("\n", "#", phash, {"#": "\n"}),
        )

    def test_lex_comment(self):
        pfn = dict(state=Lexer.Preserve.FALSE, end=None)
        pcom = dict(state=Lexer.Preserve.COMMENT, end="*/")
        self.assertEqual(
            ("", pfn),
            Lexer.lex_comment(
                "a",
                "b",
                "c",
                "",
                pfn,
                dict(
                    single_comments={"k": "v"},
                    multi_comments=(("/*", "*/"),),
                    multi_chars={"/", "*"},
                ),
            ),
        )

        self.assertEqual(
            ("/*", pcom),
            Lexer.lex_comment(
                "*",
                "/",
                "c",
                "",
                pfn,
                dict(
                    single_comments={"k": "v"},
                    multi_comments=(("/*", "*/"),),
                    multi_chars={"/", "*"},
                ),
            ),
        )


class TestLexer(unittest.TestCase):
    def setUp(self):
        def get_tokens(s):
            tokens = list()
            lex = Lexer.lexer(s)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        self.get_tokens = get_tokens

    def test_plain(self):
        s = "This is a test."
        tokens = s.split()
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_newline(self):
        s = "This \n is  a\ttest."
        tokens = ["This", "is", "a", "test."]
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_reserved(self):
        s = "Te=st"
        tokens = ["Te", "=", "st"]
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_comment(self):
        s = "There is a /* comment */"
        tokens = ["There", "is", "a", "/* comment */"]
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = "/* At */ the beginning"
        tokens = ["/* At */", "the", "beginning"]
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = "In/*the*/middle."
        tokens = ["In", "/*the*/", "middle."]
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_custom_comment(self):
        def get_tokens(s):
            tokens = list()
            g = PVLGrammar()
            g.comments = (("/*", "*/"), ("#", "\n"))
            lex = Lexer.lexer(s, g=g)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        s = "There is a # comment"
        tokens = ["There", "is", "a", "# comment"]
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = "There is a # comment \n then more"
        tokens = ["There", "is", "a", "# comment \n", "then", "more"]
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = "# Leading \n then \n more"
        tokens = ["# Leading \n", "then", "more"]
        out = get_tokens(s)
        self.assertEqual(tokens, out)

    def test_omni_comment(self):
        def get_tokens(s):
            tokens = list()
            lex = Lexer.lexer(s, g=OmniGrammar())
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        s = """
        /* comment on line */
        # here is a line comment
        /* here is a multi-
        line comment */
        foo = bar /* comment at end of line */
        weird/* in the */=/*middle*/comments
        baz = bang # end line comment
        End
    """
        out = get_tokens(s)
        self.assertEqual(
            [
                "/* comment on line */",
                "# here is a line comment\n",
                "/* here is a multi-\n        line comment */",
                "foo",
                "=",
                "bar",
                "/* comment at end of line */",
                "weird",
                "/* in the */",
                "=",
                "/*middle*/",
                "comments",
                "baz",
                "=",
                "bang",
                "# end line comment\n",
                "End",
            ],
            out,
        )

    def test_quotes(self):
        pairs = (
            (
                '"This is quoted." Notquoted',
                ['"This is quoted."', "Notquoted"],
            ),
            (
                "\"These 'are' inner\" quotes",
                ["\"These 'are' inner\"", "quotes"],
            ),
            (
                "'Other # reserved <chars>' outside",
                ["'Other # reserved <chars>'", "outside"],
            ),
        )
        for p in pairs:
            with self.subTest(pairs=p):
                out = self.get_tokens(p[0])
                self.assertEqual(p[1], out)

    # def test_foo(self):
    #     out = self.get_tokens("""single = 'single"quotes'
    #     mixed = 'mixed"\\'quotes'
    #     number = '123'
    # """)

    def test_numeric(self):
        pairs = (
            ("Number: +79", ["Number:", "+79"]),
            ("Binary: +2#0101#", ["Binary:", "+2#0101#"]),
            ("Scientific_notation: 2e+2", ["Scientific_notation:", "2e+2"]),
        )
        # ('Binary: +2#0101#', ['Binary:', '+2', '#', '0101', '#']))
        for p in pairs:
            with self.subTest(pairs=p):
                out = self.get_tokens(p[0])
                self.assertEqual(p[1], out)

    def test_send(self):
        s = "One Two Three"
        tokens = Lexer.lexer(s)
        for t in tokens:
            if t == "Two":
                tokens.send(t)  # return the Token to the generator
                break

        self.assertEqual("Two", next(tokens))

    def test_lex_char(self):
        g = PVLGrammar()
        p = dict(state=Lexer.Preserve.FALSE, end="end")
        self.assertEqual(
            ("a", p),
            Lexer.lex_char(
                "a",
                "b",
                "c",
                "",
                p,
                g,
                dict(
                    chars={"k", "v", "/", "*"},
                    single_comments={"k": "v"},
                    multi_chars={"/", "*"},
                ),
            ),
        )

        self.assertRaises(
            ValueError,
            Lexer.lex_char,
            "a",
            "b",
            "c",
            "",
            dict(state="bogus preserve state", end="end"),
            g,
            dict(
                chars={"k", "v", "/", "*"},
                single_comments={"k": "v"},
                multi_chars={"/", "*"},
            ),
        )

    def text_lexer_allowed(self):
        self.assertRaises(LexerError, Lexer.lexer(chr(7)))

    def test_lexer_recurse(self):
        def foo(tokens):
            two = list()
            for t in tokens:
                if t == "f":
                    break
                two.append(t)
            return two

        lex = Lexer.lexer("a b c d e f g h")
        one = list()
        for t in lex:
            if t == "c":
                two = foo(lex)
            else:
                one.append(t)

        self.assertEqual(["a", "b", "g", "h"], one)
        self.assertEqual(["d", "e"], two)
