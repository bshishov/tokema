from typing import Tuple, Union

__all__ = [
    'Rule',
    'Query',
    'TerminalQuery',
    'ReferenceQuery'
]


class TerminalQuery:
    def __hash__(self):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class ReferenceQuery:
    __slots__ = 'reference'

    def __init__(self, reference: str):
        self.reference = reference

    def __hash__(self):
        return hash(self.reference)

    def __str__(self):
        return f'<{self.reference}>'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.reference!r})'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.reference == other.reference
        return False


Query = Union[TerminalQuery, ReferenceQuery]


class Rule:
    __slots__ = 'production', 'queries'

    def __init__(self, production: str, queries: Tuple[Query, ...]):
        self.production = production
        self.queries = queries

    def __str__(self):
        matchers_fmt = ' '.join(str(m) for m in self.queries)
        return f'{self.production} = {matchers_fmt}'

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.production} with {len(self.queries)} queries>'
