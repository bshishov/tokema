from collections import defaultdict
import time
from contextlib import contextmanager

__all__ = [
    'print_tree',
    'print_parented_tree',
    'benchmark'
]


def print_tree(
        root,
        value_fn,
        iter_children_fn,
        marker_str="├─ ",
        level_markers=(),
        is_last: bool = True
):
    padding = " "*len(marker_str)
    connection_str = "│" + padding[:-1]
    level = len(level_markers)
    mapper_fn = (lambda draw: connection_str if draw else padding)
    markers = "".join(map(mapper_fn, level_markers[:-1]))

    if not is_last:
        markers += marker_str if level > 0 else ""
    else:
        markers += "└─ " if level > 0 else ""
    print(f"{markers}{value_fn(root)}")
    children = list(iter_children_fn(root))
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        print_tree(
            root=child,
            value_fn=value_fn,
            iter_children_fn=iter_children_fn,
            marker_str=marker_str,
            level_markers=[*level_markers, not is_last],
            is_last=is_last
        )


def print_parented_tree(nodes_iterator, parent_fn, value_fn, key_fn=lambda x: x):
    """ Prints a tree that is defined by parent referencing

    :param nodes_iterator: All-nodes iterator
    :param parent_fn: Function of node that returns a parent node for a given node
    :param value_fn: Function of node that returns a printable value for a given node
    :param key_fn: Function of node that returns hashable key for a given node
    """

    def _iter_node_parent_pairs(_n):
        _p = parent_fn(_n)
        yield _n, _p
        if _p:
            yield from _iter_node_parent_pairs(_p)

    nodes_normalized = defaultdict(dict)
    for node in nodes_iterator:
        for n, parent in _iter_node_parent_pairs(node):
            if parent is None:
                key = None
            else:
                key = key_fn(parent)
            nodes_normalized[key][key_fn(n)] = n

    root = next(iter(nodes_normalized[None].values()))

    def _iter_children(_n):
        return nodes_normalized[key_fn(_n)].values()

    print_tree(
        root=root,
        value_fn=value_fn,
        iter_children_fn=_iter_children
    )


@contextmanager
def benchmark(name: str):
    started = time.time()
    yield
    elapsed = (time.time() - started) * 1000
    print(f'{name} finished in {elapsed:.2f} ms')
