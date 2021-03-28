from tokema import *
from tokema.text import *
from tokema.utils import benchmark

rules = parse_rules_from_string("""
    ROOT = <S> {EOF}
    S = <NP> <VP>
    NP = det n
    NP = n
    NP = <NP> <PP>
    VP = v <NP>
    PP = p <NP>
""")

with benchmark('Table building'):
    table = build_text_parsing_table(rules, verbose=True)


tokens = ['det', 'n', 'v', 'n', 'det', 'p', 'n', EOF_TOKEN]
print(f'Parsing: {tokens}')

with benchmark('Parsing'):
    parses = parse(tokens, table, verbose=False)

for p in parses:
    print_parse_node(p)
