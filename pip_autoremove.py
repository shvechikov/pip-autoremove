from __future__ import print_function

import optparse

import pip
from pkg_resources import working_set, get_distribution


__version__ = '0.6.0'

try:
    raw_input
except NameError:
    raw_input = input


def autoremove(names, yes=False):
    start = set(map(get_distribution, names))
    graph = get_graph()
    dead = find_all_dead(graph, start)
    for d in start:
        show_tree(d, dead)
    if dead and (yes or confirm("Uninstall (y/N)?")):
        for d in dead:
            remove_dist(d)


def show_tree(dist, dead, indent=0):
    print(' ' * 4 * indent, end='')
    show_dist(dist)
    for req in requires(dist):
        if req in dead:
            show_tree(req, dead, indent + 1)


def find_all_dead(graph, start):
    return fixed_point(lambda d: find_dead(graph, d), start)


def find_dead(graph, dead):

    def is_killed_by_us(node):
        succ = graph[node]
        return succ and not (succ - dead)

    return dead | set(filter(is_killed_by_us, graph))


def fixed_point(f, x):
    while True:
        y = f(x)
        if y == x:
            return x
        x = y


def confirm(prompt):
    return raw_input(prompt) == 'y'


def show_dist(dist):
    print('%s %s (%s)' % (dist.project_name, dist.version, dist.location))


def remove_dist(dist):
    pip.main(['uninstall', '-y', dist.project_name])
    # Avoid duplicate output caused by pip.logger.consumers being configured
    # over and over again
    pip.logger.consumers = []


def get_graph():
    g = dict((dist, set()) for dist in working_set)
    for dist in working_set:
        for req in requires(dist):
            g[req].add(dist)
    return g


def requires(dist):
    return map(get_distribution, dist.requires())


def main(argv=None):
    parser = create_parser()
    (opts, args) = parser.parse_args(argv)
    autoremove(args, yes=opts.yes)


def create_parser():
    parser = optparse.OptionParser(
        usage='usage: %prog [OPTION]... [NAME]...',
        version='%prog ' + __version__,
    )
    parser.add_option(
        '-y', '--yes', action='store_true', default=False,
        help="don't ask for confirmation of uninstall deletions.")
    return parser


if __name__ == '__main__':
    main()
