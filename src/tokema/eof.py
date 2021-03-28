"""EOF (End of file) - special token, query and resolver for this specific token

Use of this token is optional, but it helps parser to identify the end to trigger productions.
EOF is a special object to distinguish from any text / None or other tokens that could be valid.
"""

from .grammar import TerminalQuery
from .table import Resolver

__all__ = [
    'EOF_TOKEN',
    'EofQuery',
    'EofResolver'
]


class Eof:
    def __str__(self):
        return '{EOF}'

    def __repr__(self):
        return 'EOF'


EOF_TOKEN = Eof()


class EofQuery(TerminalQuery):
    QUERY_SYMBOL = '{EOF}'

    def __hash__(self):
        return hash(self.QUERY_SYMBOL)

    def __str__(self):
        return self.QUERY_SYMBOL

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class EofResolver(Resolver):
    def __init__(self):
        self.doc = None

    def add_query(self, query: TerminalQuery, doc):
        if isinstance(query, EofQuery):
            self.doc = doc

    def resolve(self, token):
        if token is EOF_TOKEN:
            return self.doc
        return None
