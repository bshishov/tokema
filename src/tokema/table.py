from typing import Optional, Tuple, Mapping, Dict, List, Set, Iterable, Union, Any
from collections import defaultdict

from .grammar import Rule, TerminalQuery, ReferenceQuery, Query


__all__ = [
    'ShiftToStateAction',
    'ReduceByRuleAction',
    'Action',
    'ParsingTable',
    'Resolver',
    'build_parsing_table'
]


class ShiftToStateAction:
    __slots__ = 'state'

    def __init__(self, state: int):
        self.state = state

    def __str__(self):
        return f'S({self.state})'

    def __repr__(self):
        return f'{self.__class__.__name__}(state={self.state!r})'


class ReduceByRuleAction:
    __slots__ = 'rule'

    def __init__(self, rule: Rule):
        self.rule = rule

    def __str__(self):
        return f'R({self.rule})'

    def __repr__(self):
        return f'{self.__class__.__name__}(rule={self.rule!r})'


Action = Union[ShiftToStateAction, ReduceByRuleAction]


class Item:
    __slots__ = 'rule', 'expected_token_index', '_hash'

    def __init__(self, rule: Rule, expected_token_index: int):
        self.rule = rule
        self.expected_token_index = expected_token_index

        # Precomputed hash for performance
        self._hash = hash((rule, expected_token_index))

    def __str__(self):

        def _iter():
            for t in self.rule.queries[:self.expected_token_index]:
                yield str(t)
            yield '•'
            for t in self.rule.queries[self.expected_token_index:]:
                yield str(t)

        tokens = ' '.join(_iter())
        return f'{self.rule.production}={tokens}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.rule!r}, {self.expected_token_index!r})'

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, Item):
            return self._hash == other._hash
        return False


class State:
    def __init__(self, id: int, items: Tuple[Item]):
        self.id = id
        self.items = items

        # Precomputed hash for performance
        self._hash = hash(items)

    def __hash__(self):
        return self._hash

    def __iter__(self):
        return iter(self.items)

    def __str__(self):
        return ', '.join(str(i) for i in self.items)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._hash == other._hash
        return False


class Resolver:
    """Base class for query resolution"""

    def add_query(self, query: TerminalQuery, doc):
        """Registers query if accepted by resolver"""
        raise NotImplementedError

    def resolve(self, token):
        """Tries to resolve token, returning None otherwise"""
        raise NotImplementedError


class ParsingTable:
    def __init__(self, resolvers: List[Resolver]):
        self._goto: Mapping[int, Dict[str, int]] = defaultdict(dict)
        self._resolvers = resolvers
        self._action_pre_table = defaultdict(dict)

    def add_action(self, state: int, terminal_query: TerminalQuery, action: Action):
        entry = self._action_pre_table[terminal_query]  # e.g. get_or_create_entry(query)
        entry[state] = action
        for resolver in self._resolvers:
            resolver.add_query(terminal_query, entry)

    def add_goto(self, state: int, variable: str, next_state: int):
        self._goto[state][variable] = next_state

    def get_action(self, state: int, input_token) -> Tuple[Optional[Action], Any]:
        # Calling each resolver and ask them if they can handle give input token
        for resolver in self._resolvers:
            entry = resolver.resolve(input_token)
            if entry is not None:
                meta = None
                if isinstance(entry, tuple):
                    # Extracting additional metadata information from the resolver
                    entry, meta = entry
                return entry.get(state), meta
        return None, None

    def get_goto_state(self, state: int, variable: str) -> Optional[int]:
        return self._goto[state].get(variable)

    def get_shift_state(self, state: int, look_ahead_token) -> Tuple[Optional[int], Any]:
        action, meta = self.get_action(state, look_ahead_token)
        if isinstance(action, ShiftToStateAction):
            return action.state, meta
        return None, None

    def get_rule_reduction(self, state: int, look_ahead_token) -> Optional[Rule]:
        action, _ = self.get_action(state, look_ahead_token)
        if isinstance(action, ReduceByRuleAction):
            return action.rule
        return None


def expand_items(items: List[Item], rules: List[Rule], idx: int = -1):
    """Closure: Expands `items` from rules by its expectation tokens from last item recursively

    `items` array is modified during execution to reduce list allocations
    """
    root = items[idx]
    if root.expected_token_index < len(root.rule.queries):
        expected_token = root.rule.queries[root.expected_token_index]
        if isinstance(expected_token, ReferenceQuery):
            for rule in rules:
                if rule.production == expected_token.reference:

                    # Checks if the items we are going to build is already in the items array
                    # This could happen if we have multiple rules with same reference expectation
                    # A = . <X>
                    # B = . <X>
                    # So we need to check if <X> is already expanded
                    if not item_is_in_collection(rule, 0, items):
                        items.append(Item(rule=rule, expected_token_index=0))

                        # Expand further recursively (depth-first)
                        expand_items(items, rules)


def item_is_in_collection(
        rule: Rule,
        expected_token_index: int,
        collection: Iterable[Item]
) -> bool:
    for item in collection:
        if rule == item.rule and expected_token_index == item.expected_token_index:
            return True
    return False


def find_state_containing_items(states: List[State], items: Iterable[Item]) -> Optional[State]:
    for state in states:
        all_items_present_in_state = True
        for item in items:
            if not item_is_in_collection(item.rule, item.expected_token_index, state.items):
                all_items_present_in_state = False
                break
        if all_items_present_in_state:
            return state
    return None


def expand_states(states: List[State], rules: List[Rule], transitions: Set[Tuple]):
    # TODO: Optimize performance
    root = states[-1]

    for transition_token, new_core_items in iter_transitions_from_state(root):

        # Expand all items for each basic core item
        # Because multiple items could produce same new state using same transition token
        for i in range(len(new_core_items)):
            expand_items(new_core_items, rules, idx=i)

        new_state = find_state_containing_items(states, new_core_items)
        if not new_state:
            # There is no state with these items - create a new one
            new_state = State(id=len(states), items=tuple(new_core_items))
            states.append(new_state)

            # expand new state recursively (depth-first)
            expand_states(states, rules, transitions)

        # Add transition in any case
        transitions.add((root.id, transition_token, new_state.id))


def iter_transitions_from_state(state: State) -> Iterable[Tuple[Query, List[Item]]]:
    """Iterates transitions from state returning transition token and list of new state's core
    items
    """

    # TODO: REFACTOR
    transitions = defaultdict(list)
    for item in state:

        # If there is expectation in item
        if item.expected_token_index < len(item.rule.queries):
            transition_token = item.rule.queries[item.expected_token_index]

            # Create new item from current by shifting expectation token index (the dot) right
            new_state_root = Item(
                rule=item.rule,
                expected_token_index=item.expected_token_index + 1
            )
            transitions[transition_token].append(new_state_root)

    return transitions.items()


def build_parsing_table(
        rules: List[Rule],
        resolvers: Iterable[Resolver],
        verbose: bool = False
) -> ParsingTable:
    terminal_queries: Set[TerminalQuery] = set()

    # Collect all terminal queries
    for rule in rules:
        for token in rule.queries:
            if isinstance(token, TerminalQuery):
                terminal_queries.add(token)

    # Create root state
    root_rule = rules[0]
    root_item = Item(rule=root_rule, expected_token_index=0)
    root_state_items = [root_item]
    expand_items(root_state_items, rules)
    root_state = State(0, tuple(root_state_items))

    # Expand all states and transitions
    states = [root_state]
    transitions: Set[Tuple[int, TerminalQuery, int]] = set()
    expand_states(states, rules, transitions)

    # Create terminal token resolution table
    table = ParsingTable(resolvers=list(resolvers))

    if verbose:
        print('States:')
    for state in states:
        for item in state.items:

            if item.expected_token_index >= len(item.rule.queries):
                action = ReduceByRuleAction(item.rule)
                for t in terminal_queries:
                    table.add_action(state.id, t, action)

        if verbose:
            print(f'{state.id}\t{state}')

    if verbose:
        print('Edges:')
    for from_id, token, to_id in transitions:
        if verbose:
            print(f'{from_id} {token} {to_id}')
        if isinstance(token, ReferenceQuery):
            table.add_goto(from_id, token.reference, to_id)
        elif isinstance(token, TerminalQuery):
            table.add_action(from_id, token, ShiftToStateAction(to_id))

    return table
