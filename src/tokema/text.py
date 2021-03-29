"""Common text-based pipeline and set of queries and resolvers"""

from typing import Iterable, List

from .grammar import *
from .table import *
from .eof import EOF_TOKEN, EofQuery, EofResolver

__all__ = [
    'TextQuery',
    'IntQuery',
    'FloatQuery',
    'ExactTextResolver',
    'CaseInsensitiveTextResolver',
    'IntResolver',
    'FloatResolver',
    'LevenshteinTextResolver',
    'parse_rules_from_string',
    'build_text_parsing_table',
    'tokenize'
]


class TextQuery(TerminalQuery):
    __slots__ = 'text', 'case_sensitive'

    def __init__(self, text: str, case_sensitive: bool = True):
        self.text = text
        self.case_sensitive = case_sensitive

    def __hash__(self):
        return hash(self.text)

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'{self.__class__.__name__}({self.text!r})'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.text == other.text
        return False


class IntQuery(TerminalQuery):
    def __hash__(self):
        return hash(self.__class__.__name__)

    def __str__(self):
        return '{int}'

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class FloatQuery(TerminalQuery):
    def __hash__(self):
        return hash(self.__class__.__name__)

    def __str__(self):
        return '{float}'

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class ExactTextResolver(Resolver):
    __slots__ = 'index'

    def __init__(self):
        self.index = {}

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, TextQuery) and query.case_sensitive:
            self.index[query.text] = doc

    def resolve(self, token):
        if isinstance(token, str):
            return self.index.get(token)


class CaseInsensitiveTextResolver(Resolver):
    __slots__ = 'index'

    def __init__(self):
        self.index = {}

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, TextQuery) and not query.case_sensitive:
            self.index[query.text.lower()] = doc

    def resolve(self, token):
        if isinstance(token, str):
            return self.index.get(token.lower())


class IntResolver(Resolver):
    def __init__(self):
        self.doc = None

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, IntQuery):
            self.doc = doc

    def resolve(self, token):
        try:
            value = int(token)
            return self.doc, value
        except (ValueError, TypeError):
            return None


class FloatResolver(Resolver):
    def __init__(self):
        self.doc = None

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, FloatQuery):
            self.doc = doc

    def resolve(self, token):
        try:
            value = float(token)
            return self.doc, value
        except (ValueError, TypeError):
            return None


def _iter_levenshtein_distance1_variations(original: str, alphabet: str) -> Iterable[str]:
    original = original.lower()
    yield original

    for i in range(len(original)):
        # Deletion
        yield original[:i] + original[i + 1:]

        for ch in alphabet:
            # Substitution
            yield original[:i] + ch + original[i:]

            # Insertion
            yield original[:i] + ch + original[i+1:]

    # Last Insertion
    for ch in alphabet:
        yield original + ch


class LevenshteinTextResolver(Resolver):

    def __init__(self, min_len: int = 4):
        self.min_len = min_len
        self.index = {}
        self.alphabet: str = ' abcdefghijklmnopqrstuvwxyz' \
                             'абвгдеёжзгдийклмнопрстуфхцчшщъыьэюя' \
                             ',./1234567890-=\\'

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, TextQuery):
            text = query.text.lower()
            if len(text) >= self.min_len:
                for variation in _iter_levenshtein_distance1_variations(text, self.alphabet):
                    self.index[variation] = doc

    def resolve(self, token):
        if isinstance(token, str):
            return self.index.get(token.lower())


def _parse_rules_from_line(
        rule: str,
        rule_sep: str,
        productions_sep: str,
        reference_start: str,
        reference_end: str,
) -> Iterable[Rule]:
    sep_idx = rule.find(rule_sep)
    if sep_idx < 0:
        raise ValueError(f'Invalid rule "{rule}", missing separator "{rule_sep}"')
    production = rule[:sep_idx].strip()

    if not production:
        raise ValueError(f'Invalid rule "{rule}": missing production')

    args_collection = rule[sep_idx + len(rule_sep):]

    if not args_collection:
        raise ValueError(f'Invalid rule "{rule}": missing args')

    for args_str in args_collection.split(productions_sep):
        args = args_str.strip().split()

        if not args:
            raise ValueError(f'Invalid rule "{rule}": empty argument in production')

        tokens = []
        for a in args:
            a = a.strip()
            if a.startswith(reference_start) and a.endswith(reference_end):
                tokens.append(ReferenceQuery(a[len(reference_start):-len(reference_end)]))
            elif a == EofQuery.QUERY_SYMBOL:
                tokens.append(EofQuery())
            elif a == '{int}':
                tokens.append(IntQuery())
            elif a == '{float}':
                tokens.append(FloatQuery())
            else:
                tokens.append(TextQuery(a))

        yield Rule(production=production, queries=tuple(tokens))


def parse_rules_from_string(
        raw: str,
        rule_sep: str = '=',
        productions_sep: str = '|',
        line_comment: str = '#',
        reference_start: str = '<',
        reference_end: str = '>',
) -> List[Rule]:
    rules = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(line_comment):
            continue
        for rule in _parse_rules_from_line(
            rule=line,
            rule_sep=rule_sep,
            productions_sep=productions_sep,
            reference_start=reference_start,
            reference_end=reference_end
        ):
            rules.append(rule)
    return rules


def build_text_parsing_table(
        rules: List[Rule],
        verbose: bool = False,
        additional_resolvers: Iterable[Resolver] = None
) -> ParsingTable:
    """Construct text-parsing table for parsing text-based tokens

    Special set of text-resolvers is added
    """

    resolvers = [
        ExactTextResolver(),
        CaseInsensitiveTextResolver(),
        #LevenshteinTextResolver(),
        IntResolver(),
        FloatResolver(),
        EofResolver()
    ]

    if additional_resolvers:
        for r in additional_resolvers:
            resolvers.append(r)

    return build_parsing_table(rules=rules, verbose=verbose, resolvers=resolvers)


def tokenize(src: str, add_eof: bool = False) -> List[str]:
    symbols = []
    for t in src.split():
        t = t.strip()
        if t:
            symbols.append(t)

    if add_eof:
        symbols.append(EOF_TOKEN)
    return symbols
