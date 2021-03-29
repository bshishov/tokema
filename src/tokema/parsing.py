from typing import Optional, List, Iterable, Union
from itertools import chain

from .grammar import Rule
from .utils import print_tree, print_parented_tree
from .table import ParsingTable


__all__ = [
    'parse',
    'Symbol',
    'ParseNode',
    'print_parse_node'
]


class Symbol:
    """Input token with additional parsing-related information

    :param position: Token position index
    :param value: Original token value
    :param meta: Addition meta information from resolver
    """
    __slots__ = 'position', 'value', 'meta'

    def __init__(self, value, position: int, meta=None):
        self.position = position
        self.value = value
        self.meta = meta

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value!r}, {self.position!r}, {self.meta!r})'


class ParseNode:
    __slots__ = 'rule', 'args'

    def __init__(self, rule: Rule, args: List[Union['ParseNode', Symbol]]):
        """
        :param rule: Rule used to produce this node
        :param args: Symbols that matched rule queries
        """
        self.rule = rule
        self.args = args

    def __len__(self):
        return len(self.args)

    def __getitem__(self, item):
        return self.args.__getitem__(item)

    def __iter__(self):
        return self.args.__iter__()

    def __str__(self):
        args_fmt = ', '.join(str(a) for a in self.args)
        return f'{self.rule.production}({args_fmt})'

    def __repr__(self):
        return f'{self.__class__.__name__}(rule={self.rule!r}, args={self.args!r})'


class _Node:
    """GLR Parser state node"""

    __slots__ = 'state', 'start_pos', 'end_pos', 'symbol', 'parent', 'skipped_symbols'

    def __init__(
            self,
            state: int,
            start_pos: int,
            end_pos: int,
            symbol: Union[Symbol, ParseNode, None],
            parent: Optional['_Node'] = None,
            skipped_symbols: int = 0,
    ):
        self.state = state
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.symbol = symbol
        self.parent = parent
        self.skipped_symbols = skipped_symbols

    def __repr__(self):
        return f'<ParserNode {self.state} {self.symbol}>'


def parse(
        input_tokens: Iterable,
        table: ParsingTable,
        beam_limit: int = 100,
        verbose: bool = False,
        root_production: str = 'ROOT',
) -> List[ParseNode]:
    """Parses input steam of tokens of any type (that table support)

    Parsing algorithm is designed based on GLR* with noise skipping.

    For basic algorithm understanding read:
        Lavie, Alon, and Masaru Tomita.
        "10. GLR*-AN EFFICIENT NOISE-SKIPPING PARSING ALGORITHM FOR CONTEXT-FREE GRAMMARS."
        Recent Advances in Parsing Technology 1 (1996): 183.

    Matching tokens with queries (matchers) happens inside the table.

    :param input_tokens: Stream of input tokens (i.e. strings)
    :param table: GLR-compatible Parsing table
    :param beam_limit: inactive nodes size limit, 0 - no limit
    :param verbose: Algorithm prints a lot of debug output if True
    :param root_production:

    :returns: List of found parses if any
    """

    # GLR Parse tree root node
    root = _Node(symbol=None, state=0, start_pos=-1, end_pos=0)

    # Input stream variables
    token_stream = iter(enumerate(input_tokens))
    try:
        look_ahead_token_position, look_ahead_token = next(token_stream)
    except StopIteration:
        # Empty token stream
        return []

    # Non-active node, states that will be shifted by input token on the shift phase
    inactive_nodes: List[_Node] = [root]

    # Nodes queue to check for reductions.
    # Each reduction produces a new node and adds it to the queue
    # Reductions happens until queue is empty
    active_nodes_queue: List[_Node] = []

    # Parsing step
    step = 0

    while True:
        step += 1

        if verbose:
            print(f'\n------------- STEP {step} ---------------\n')
            _print_parser_state(inactive_nodes=inactive_nodes, active_nodes=active_nodes_queue)
            print(f'\n--- SHIFTING {look_ahead_token} \n')

        # Shift phase
        for node in inactive_nodes:
            shift_to_state, meta = table.get_shift_state(node.state, look_ahead_token)
            if shift_to_state:
                new_node = _Node(
                    parent=node,
                    symbol=Symbol(
                        value=look_ahead_token,
                        position=look_ahead_token_position,
                        meta=meta
                    ),
                    state=shift_to_state,
                    start_pos=look_ahead_token_position,
                    end_pos=look_ahead_token_position + 1,
                    skipped_symbols=look_ahead_token_position - node.end_pos
                )
                inactive_nodes.append(new_node)  # Add to graph
                active_nodes_queue.append(new_node)  # Enqueue for potential reductions

        if verbose:
            _print_parser_state(inactive_nodes=inactive_nodes, active_nodes=active_nodes_queue)
            print(f'\n--- REDUCING')

        # Reduce phase
        reduction_results: List[_Node] = []
        while active_nodes_queue:
            node = active_nodes_queue.pop()

            rule = table.get_rule_reduction(node.state, look_ahead_token)
            if rule:
                skipped_symbols = 0
                production_args = []
                production_root = node
                for _ in range(len(rule.queries)):
                    production_args.insert(0, production_root.symbol)
                    skipped_symbols += production_root.skipped_symbols
                    production_root = production_root.parent

                next_state = table.get_goto_state(production_root.state, rule.production)
                new_node = _Node(
                    state=next_state,
                    symbol=ParseNode(rule=rule, args=production_args),
                    parent=production_root,
                    start_pos=production_root.start_pos,
                    end_pos=node.end_pos,
                    skipped_symbols=skipped_symbols
                )

                # ---- LOCAL AMBIGUOUS NODE CHECK ----
                # Ambiguous nodes - nodes that share production_root
                amb_reduction_results = []
                inamb_reduction_results = []
                for n in reduction_results:
                    if n.parent == new_node.parent and isinstance(n.symbol, ParseNode):
                        amb_reduction_results.append(n)
                    else:
                        inamb_reduction_results.append(n)

                if amb_reduction_results:
                    if verbose:
                        print(f'--- RESOLVING {len(amb_reduction_results)} AMBIGUOUS NODES!')

                    new_node_is_best = True
                    resolved_node = new_node

                    for n in amb_reduction_results:
                        if n.skipped_symbols < new_node.skipped_symbols:
                            resolved_node = n
                            new_node_is_best = False

                    if new_node_is_best:
                        # TODO: Should we keep ambiguous nodes in the graph or replace it?

                        active_nodes_queue.append(new_node)
                        #inamb_reduction_results.append(new_node)
                        #reduction_results = inamb_reduction_results
                        reduction_results.append(new_node)

                    else:
                        if verbose:
                            print(f'New node {new_node} '
                                  f'(with {new_node.skipped_symbols} skipped) '
                                  f'is worse than {resolved_node} '
                                  f'(with {resolved_node.skipped_symbols} skipped),'
                                  f' skipping')

                else:
                    active_nodes_queue.append(new_node)
                    reduction_results.append(new_node)

                # # ---- END OF LOCAL AMBIGUOUS NODE CHECK ----

                # Default
                #active_nodes_queue.append(new_node)
                #reduction_results.append(new_node)

        for node in reduction_results:
            inactive_nodes.append(node)

        try:
            look_ahead_token_position, look_ahead_token = next(token_stream)
        except StopIteration:
            # End of stream
            break

        # Limiting
        inactive_nodes[:] = inactive_nodes[-beam_limit:]

    # Result gathering
    parses: List[ParseNode] = [
        n.symbol for n in inactive_nodes
        if (
                isinstance(n.symbol, ParseNode) and
                n.symbol.rule.production == root_production
        )
    ]
    # parses = sorted(parses, key=lambda _: _.skipped_symbols)
    # parses = sorted(parses, key=lambda x: x.end_pos - x.start_pos)  # Better sorting ?

    if verbose:
        print('\n--- RESULT ---')
        for n in parses:
            print()
            print_parse_node(n)

    return parses


def _print_parser_state(active_nodes: Iterable[_Node], inactive_nodes: Iterable[_Node]):
    nodes_it = chain(inactive_nodes, active_nodes)

    def _node_to_str(n: _Node):
        node_type_fmt = '*'
        for an in active_nodes:
            if id(n) == id(an):
                node_type_fmt = '@'
                break

        return f'{node_type_fmt} {n.state} {n.symbol}'

    print_parented_tree(nodes_it, lambda n: n.parent, _node_to_str, key_fn=id)


def _symbol_value(s):
    if isinstance(s, ParseNode):
        return s.rule.production
    return str(s)


def _iter_symbol_children(s):
    if isinstance(s, ParseNode):
        return s.args
    return []


def print_parse_node(n: ParseNode):
    print_tree(n, value_fn=_symbol_value, iter_children_fn=_iter_symbol_children)
