from tokema import *

# Define grammar
# NOTE: you can also define it using python classes only or create you own grammar syntax
rules = parse_rules_from_string("""
ROOT = <EXPR>
EXPR = {float} + {float}
""")

# Parsing table construction
table = build_text_parsing_table(rules)

# Input tokens
# NOTE: In real application you should use some real tokenizer (like nltk)
tokens = 'this will be ignored 3.1415 and + this 4e-10'.split()

# Actual parsing using token stream and parsing table
# There may be multiple parses (not in this oversimplified scenario) so parse returns a list
results = parse(tokens, table)

for result in results:
    # Here you can access the parsed AST (abstract syntax tree)
    print(result)  # ROOT(EXPR(3.1415, +, 4e-10))
