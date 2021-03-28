"""Example of enhancing original parser with stemming using pystemmer"""
from Stemmer import Stemmer
from tokema import *


class StemmerResolver(Resolver):
    """Additional resolver that will try to use stemmed text for reverse index lookups"""

    def __init__(self, stemmer: Stemmer):
        self.index = {}
        self.stemmer = stemmer

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, TextQuery):
            s = self.stemmer.stemWord(query.text)
            self.index[s] = doc

    def resolve(self, token):
        if isinstance(token, str):
            s = self.stemmer.stemWord(token)
            return self.index.get(s)
        return None


stemmer_resolver = StemmerResolver(Stemmer('russian'))

rules = parse_rules_from_string("""
SENTENCE = <WORDS> .

WORDS = <WORDS> <WORD>
WORDS = <WORD>

WORD = слово
WORD = другой
WORD = это
""")

table = build_text_parsing_table(rules, additional_resolvers=[stemmer_resolver])

text = 'эти слова а еще и другие слова которые другим словом - слово .'

parse(text.split(), table, verbose=True, root_production='SENTENCE')
