"""Russian fairy tail example - trying to extract sentence structure"""

import re
from tokema import *
from tokema.utils import benchmark

TEXT = """
Старый солдат шёл на побывку. Притомился в пути, есть хочется. Дошёл до деревни, постучал в крайнюю избу:
- Пустите отдохнуть дорожного человека! Дверь отворила старуха.
- Заходи, служивый.
- А нет ли у тебя, хозяюшка, перекусить чего? У старухи всего вдоволь, а солдата поскупилась накормить, прикинулась сиротой.
- Ох, добрый человек, и сама сегодня ещё ничего не ела: нечего.
- Ну, нет так нет,- солдат говорит. Тут он приметил под лавкой топор.
- Коли нет ничего иного, можно сварить кашу и из топора.

Хозяйка руками всплеснула:
- Как так из топора кашу сварить?
- А вот как, дай-ка котёл.
Старуха принесла котёл, солдат вымыл топор, опустил в котёл, налил воды и поставил на огонь.
Старуха на солдата глядит, глаз не сводит.

Достал солдат ложку, помешивает варево. Попробовал.
- Ну, как? - спрашивает старуха.
- Скоро будет готова, - солдат отвечает, - жаль вот только, что посолить нечем.
- Соль-то у меня есть, посоли.
Солдат посолил, снова попробовал.
- Хороша! Ежели бы сюда да горсточку крупы! Старуха засуетилась, принесла откуда-то мешочек крупы.
- Бери, заправь как надобно. Заправил варево крупой. Варил, варил, помешивал, попробовал. Глядит старуха на солдата во все глаза, оторваться не может.
- Ох, и каша хороша! - облизнулся солдат.- Как бы сюда да чуток масла - было бы и вовсе объедение.
Нашлось у старухи и масло.

Сдобрили кашу.
- Ну, старуха, теперь подавай хлеба да принимайся за ложку: станем кашу есть!
- Вот уж не думала, что из топора эдакую добрую кашу можно сварить, - дивится старуха.
Поели вдвоем кашу. Старуха спрашивает:
- Служивый! Когда ж топор будем есть?
- Да, вишь, он не уварился,- отвечал солдат,- где-нибудь на дороге доварю да позавтракаю!
Тотчас припрятал топор в ранец, распростился с хозяйкою и пошёл в иную деревню.

Вот так-то солдат и каши поел и топор унёс!
"""

GRAMMAR = """
DOC = <SENTENCES> {EOF} 

SENTENCES = <SENTENCES> <S>
SENTENCES = <S>

SENTENCE_END = .
SENTENCE_END = !
SENTENCE_END = ?
SENTENCE_END = :

S = <WORDS> <SENTENCE_END>

WORDS = <WORDS> <WORD>
WORDS = <WORD>
"""

# Tokenization regex
TOKEN_PATTERN = re.compile(
    r'[^\W\d_]+|'   # any alphabetical and non-numeric
    r'\d+|'                                  # or digit
    r'[:";\'!@#$%^&*()<>?,./[\]{}\\|\-_+=]'  # or symbol
)


def tokenize(text: str):
    for match in TOKEN_PATTERN.finditer(text):
        yield match.group(0)
    yield EOF_TOKEN


if __name__ == '__main__':
    rules = parse_rules_from_string(GRAMMAR)

    # add all words (longer than 3 symbols) to rule set
    for t in tokenize(TEXT):
        if isinstance(t, str) and len(t) >= 3:
            rules.append(Rule('WORD', (TextQuery(t), )))

    with benchmark('Table construction'):
        table = build_text_parsing_table(rules, verbose=True)

    with benchmark('Parsing'):
        result = parse(tokenize(TEXT), table, root_production='DOC', verbose=False, beam_limit=20)

    for n in result:
        print_parse_node(n)
