from Stemmer import Stemmer  # you need pystemmer package for this example to work
from tokema import *
from tokema.utils import benchmark


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


class ExtendedRule(Rule):
    """Custom rule that holds metadata"""
    def __init__(self, production: str, queries, metadata):
        super().__init__(production, queries)
        self.metadata = metadata


def rule(r: str, template=None):
    """Created custom rule from string bnf-like form"""
    production, args = r.split('=')
    production: str = production.strip()

    queries = []
    for arg in args.split():
        arg: str = arg.strip()

        if arg:
            if len(arg) > 2 and arg.startswith('<') and arg.endswith('>'):
                queries.append(ReferenceQuery(arg[1:-1]))
            else:
                queries.append(TextQuery(arg))

    return ExtendedRule(production, tuple(queries), template)


def recognize(ast: ParseNode):
    """Extract metadata from ast"""
    if isinstance(ast.rule, ExtendedRule):
        return ast[0].rule.metadata
    return None


def main():
    rules = [
        rule('ROOT = <loan>'),

        rule('loan = потреб', {'type': 'consumer'}),
        rule('loan = потребительский', {'type': 'consumer'}),
        rule('loan = наличными', {'type': 'consumer'}),
        rule('loan = деньги в долг', {'type': 'consumer'}),
        rule('loan = денег в долг', {'type': 'consumer'}),

        rule('loan = на <auto>', {'type': 'auto'}),
        rule('loan = купить <auto>', {'type': 'auto'}),

        rule('loan = ипотека', {'type': 'house'}),
        rule('loan = на <prop>', {'type': 'house'}),
        rule('loan = купить <prop>', {'type': 'house'}),
        rule('loan = построить <prop>', {'type': 'house'}),

        rule('auto = тачила'),
        rule('auto = тачка'),
        rule('auto = машина'),
        rule('auto = авто'),
        rule('auto = автомобиль'),

        rule('prop = квартира'),
        rule('prop = хата'),
        rule('prop = дом'),
        rule('prop = дача'),
        rule('prop = баня'),
    ]

    stemmer = Stemmer('russian')
    stemmer_resolver = StemmerResolver(stemmer)

    with benchmark('Table construction'):
        parsing_table = build_text_parsing_table(rules, additional_resolvers=[stemmer_resolver])
    print()

    samples = [
        'Хочу кредит на машину',
        'Добрый день я бы хотел узнать можно ли у вас оформить кредит на квартиру',
        'дайте денег хочу купить машину',
        'хочу построить дом',
        'дайте денег налом в долг',
        'дайте денег на машину в долг',
    ]

    for sample in samples:
        print(sample)
        tokens = sample.split()

        with benchmark('Parsing'):
            results = parse(tokens, parsing_table)

        for ast in results:
            print(ast, recognize(ast))

        print()


if __name__ == '__main__':
    main()
