from tokema import *
from tokema.utils import *

with open('number.txt', encoding='utf-8') as f:
    rules = parse_rules_from_string(f.read())

table = build_text_parsing_table(rules)

src = 'переведи тридцать три миллиона двадцать тысяч шестнадцать рублей с карты visa'
print(f'Parsing: {src}')
tokens = src.split()

with benchmark('Parsing'):
    parses = parse(tokens, table, verbose=False, beam_limit=10)

for p in parses:
    print_parse_node(p)
