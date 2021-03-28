""" Example that manually creates rules and resolvers to show raw parser functionality """

# Core tokema parser imports
from tokema import (
    build_parsing_table,
    parse,
    Rule,
    ReferenceQuery,
    EofQuery,
    EOF_TOKEN,
    EofResolver
)

# Imports specific for string tokens and text parsing
from tokema.text import FloatQuery, FloatResolver, TextQuery, ExactTextResolver

# Create rules manually
# Note that each rule is a set of queries
rules = [
    # The rule has the name (also called production)
    # And ordered collection of queries, where each query could be viewed as a test for a
    # token, that either passes or fails. Unlike traditional parses that "expects a token"
    # tokema uses more generalized approach with all kinds of token queries
    # e.g. tokema substitutes exact token match with an abstract functional queries
    # traditional queries are:
    #   - TextQuery ("terminal")
    #   - ReferenceQuery ("non-terminal")
    Rule('ROOT', queries=(ReferenceQuery('EXPR'), EofQuery())),
    Rule('EXPR', queries=(FloatQuery(), TextQuery('+'), FloatQuery()))
]

# Create a parsing table using 2 resolvers
# FloatResolver - tries to resolve float value from text token
# ExactTextResolver - resolves text by reverse index
# EofResolver - resolver that accepts EOF token
resolvers = [FloatResolver(), ExactTextResolver(), EofResolver()]
table = build_parsing_table(rules, resolvers=resolvers, verbose=True)

# Manual "tokenization"
tokens = ['3.141592', '+', '2', EOF_TOKEN]
parses = parse(tokens, table, verbose=True)

print()
print('Parse results:')
for p in parses:
    # Rule that produced the production
    print(f'Rule: {p.rule}')

    # Arguments (child nodes)
    print(f'Args: {p.args}')
