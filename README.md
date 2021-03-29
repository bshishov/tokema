# tokema

tokema - **toke**n **ma**tching parser.

It is a pure python, zero-dependency library for building parsers. 
tokema algorithm based on Tomita's GLR* parser.

It helps to create noise-skipping grammar-based parsers at runtime and apply them to various task like 
entity extraction and token matching.

tokema algorithm is the extended version on Noise-skipping GLR* parser by Lavie Alon and Masaru Tomita:

> Lavie, Alon, and Masaru Tomita.
> "10. GLR*-AN EFFICIENT NOISE-SKIPPING PARSING ALGORITHM FOR CONTEXT-FREE GRAMMARS."
> Recent Advances in Parsing Technology 1 (1996): 183.

tokema parsing works with arbitrary tokens - chars, words, structures... you can write a parser for
token stream produced by the tokenizer of your choice.

## GLR

In general, tokema - is a GLR-based (Generalized LR) context-free parser generator which basically means 
that parser produced by tokema tries to find most suitable parses (might be multiple) given deterministic grammar.
GLR-based algorithms evaluate multiple parser states at the same time allowing to parse using incomplete and poorly structured grammars. 

## Noise-skipping

The term "noise skipping" means that parser can skip tokens it doesn't understand which is required to solve
natural language tasks.

## Extensions

Instead of direct token matching (or dictionary based) like in most traditional parsers tokema
replaces terminals and non-terminals in the grammar with queries and resolvers - 
functions that matches the input token with the given query.

By creating these functions you can construct token queries and resolvers of your choice integrating lots of cool features into your parser.
For example you can create a custom resolver matches stemmed or lemmatized text tokens.
Or create a resolver that uses custom dictionaries or even integrate a third party search backend like lucene.

## Installation

    pip install tokema
    
# Usage

Basic usage:
```python
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

    # EXPR is the first child of ROOT
    expr = result[0]

    # Convert each value to a float and make sure that result is actually correct
    assert float(expr[0].value) + float(expr[2].value) == 3.1415 + 4e-10

```

For more usage scenarios see examples folder
