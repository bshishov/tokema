from tokema import *
from tokema.utils import benchmark

with open('dota.txt', encoding='utf-8') as f:
    rules = parse_rules_from_string(f.read())

table = build_text_parsing_table(rules)

tokens = 'эй бот , плз расскажи как мне играть ' \
         'против ебаного шторма на миде и как контрить снайпера'.split()

with benchmark('Parsing'):
    results = parse(tokens, table)

for p in results:
    print_parse_node(p)
