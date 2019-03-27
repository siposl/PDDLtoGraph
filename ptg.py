#! /usr/bin/env python3
#
# PDDLtoGraph is a program to draw relatedness and causal graphs out of PDDL files.
# Copyright (C) 2019  Lars Sipos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import sys
import os
import re
import logging
import networkx as nx
import pygraphviz as pgv

try:
    import argparse
except ImportError:
    from external import argparse

from pddl.parser import Parser
import tools

NUMBER = re.compile(r'\d+')


def validator_available():
    """
    unmodified pyperplan function
    """
    return tools.command_available(['validate', '-h'])


def find_domain(problem):
    """
    This function tries to guess a domain file from a given problem file.
    It first uses a file called "domain.pddl" in the same directory as
    the problem file. If the problem file's name contains digits, the first
    group of digits is interpreted as a number and the directory is searched
    for a file that contains both, the word "domain" and the number.
    This is conforming to some domains where there is a special domain file
    for each problem, e.g. the airport domain.

    @param problem    The pathname to a problem file
    @return A valid name of a domain
    """
    dir, name = os.path.split(problem)
    number_match = NUMBER.search(name)
    number = number_match.group(0)
    domain = os.path.join(dir, 'domain.pddl')
    for file in os.listdir(dir):
        if 'domain' in file and number in file:
            domain = os.path.join(dir, file)
            break
    if not os.path.isfile(domain):
        logging.error('Domain file "{0}" can not be found'.format(domain))
        sys.exit(1)
    logging.info('Found domain {0}'.format(domain))
    return domain


def parse(domain_file, problem_file):
    """
    unmodified pyperplan function
    """
    parser = Parser(domain_file, problem_file)
    logging.info('Parsing Domain {0}'.format(domain_file))
    domain = parser.parse_domain()
    logging.info('Parsing Problem {0}'.format(problem_file))
    problem = parser.parse_problem(domain)
    logging.debug(domain)
    logging.info('{0} Predicates parsed'.format(len(domain.predicates)))
    logging.info('{0} Actions parsed'.format(len(domain.actions)))
    logging.info('{0} Objects parsed'.format(len(problem.objects)))
    logging.info('{0} Constants parsed'.format(len(domain.constants)))
    return problem


def ground(problem):
    """
    unmodified pyperplan function
    """
    logging.info('Grounding start: {0}'.format(problem.name))
    task = grounding.ground(problem)
    logging.info('Grounding end: {0}'.format(problem.name))
    logging.info('{0} Variables created'.format(len(task.facts)))
    logging.info('{0} Operators created'.format(len(task.operators)))
    return task


def build_graph_related(task, static=True, draw=True, diameter=True):
    """
    Build a relatedness graph from a task object
    :param static: Keeps static propositions by default
    :param task: task.py task object
    :param draw: Toggles the generation of a pdf file
    :param diameter: Draws one path of the length of the diameter
    """
    graph = pgv.AGraph(directed=False, size=1000)
    graph.node_attr['style']='bold'
    graph.node_attr['shape']='box'
    graph.node_attr['fixedsize']='true'
    graph.node_attr['fontsize'] = 16
    graph.node_attr['fontcolor']='#000000'
    graph.node_attr['width'] = 3

    # Remove all static propositions
    if not static:
        print("Removing statics")
        removal_list = []
        for prop in task.facts:
            if all(prop not in op.add_effects and prop not in op.del_effects for op in task.operators):
                removal_list.append(prop)

        for prop in removal_list:
            task.facts.remove(prop)

    for op in task.operators:
        for prop in task.facts:
            if prop in op.preconditions or prop in op.add_effects or prop in op.del_effects:
                try:
                    graph.get_node(prop)
                except KeyError:
                    graph.add_node(prop, color="#00e600")
                try:
                    graph.get_node(op.name)
                except KeyError:
                    graph.add_node(op.name, color="#cc0000")
                graph.add_edge(prop, op.name, minlen=15)

    remov_list = []
    for node in graph:
        if graph.degree(node) == 0:
            remov_list.append(node.name)
    graph.remove_nodes_from(remov_list)

    graph.write("graph.dot")

    # Calculate diameter and radius
    nx_graph = nx.drawing.nx_pydot.read_dot("graph.dot")

    dmtr = nx.diameter(nx_graph)
    radius = nx.radius(nx_graph)

    print("D(G)=%d" % dmtr)
    print("R(G)=%d" % radius)

    graph.add_node("D(G)=%d" % dmtr, color='invis', width=0.8)
    graph.add_node("R(G)=%d" % radius, color='invis', width=0.8)

    if diameter:
        path_graph = color_diameter(graph, nx_graph, dmtr)
        graph = path_graph

    if draw:
        graph.draw("graph.pdf", prog='dot')
    return dmtr, radius


def color_diameter(graph, graphx, diameter):
    """
    Colors the first path with diameter length inside the graph
    :param graph: An Agraph
    :param graphx: A networkx graph
    :param diameter: The length of the diameter
    :return: A colored Agraph
    """
    p = nx.periphery(graphx)
    z = nx.algorithms.single_target_shortest_path(graphx, p[0])
    print(z.values())
    for path in z.values():
        if len(path) == diameter + 1:
            print("Path")
            print(path)
            for i in range(len(path) - 1):
                edge = graph.get_edge(path[i], path[i+1])
                edge.attr['color'] = 'orange'
                edge.attr['label'] = "  " + str(i+1)
            return graph


def build_graph_causal(task):
    """
    Build a causal graph from a task object
    :param task: task.py task object
    """
    graph = pgv.AGraph(directed=True, size=1000)
    # graph.node_attr['style']='filled'
    graph.node_attr['shape']='box'
    graph.node_attr['fixedsize']='true'
    graph.node_attr['fontsize'] = 16
    graph.node_attr['fontcolor']='#000000'
    graph.node_attr['width'] = 1.5


    # Check rules for causality
    for u in task.facts:
        for v in task.facts:
            for op in task.operators:
                if u == v:
                    continue
                elif u in op.preconditions or u in op.add_effects or u in op.del_effects:
                    if v in op.add_effects or v in op.del_effects:
                        try:
                            graph.get_node(u)
                        except KeyError:
                            graph.add_node(u)
                        try:
                            graph.get_node(v)
                        except KeyError:
                            graph.add_node(v)
                        graph.add_edge(u, v, minlen=5)

    write_graph(graph)


def build_graph_rel_simple(domain, task, draw=True, diameter=True):
    """
    Build a relatedness graph with lifted actions and propositions
    :param domain: A domain class object
    :param task: A task class object
    :param draw: Toggle if a pdf-file of the graph is created
    :param diameter: Draw the path of length diameter
    :return: diameter and radius of the graph
    """
    graph = pgv.AGraph(directed=False, size=1000)
    graph.node_attr['style']='bold'
    graph.node_attr['shape']='box'
    graph.node_attr['fixedsize']='true'
    graph.node_attr['fontsize'] = 16
    graph.node_attr['fontcolor']='#000000'
    graph.node_attr['width'] = 1.5

    action_dict = {}
    for a in domain.actions:
        for op in task.operators:
            if a in op.name:
                action_dict[op.name] = a

    pred_dict = {}
    for p in domain.predicates:
        for f in task.facts:
            if p in f:
                pred_dict[f] = p

    for op in task.operators:
        for prop in task.facts:
            if prop in op.preconditions or prop in op.add_effects or prop in op.del_effects:
                try:
                    graph.get_node(pred_dict.get(prop))
                except KeyError:
                    graph.add_node(pred_dict.get(prop), color="#00e600")
                try:
                    graph.get_node(action_dict.get(op.name))
                except KeyError:
                    graph.add_node(action_dict.get(op.name), color="#cc0000")
                graph.add_edge(pred_dict.get(prop), action_dict.get(op.name), minlen=15)

    graph.write("graph.dot")

    # Calculate diameter and radius
    nx_graph = nx.drawing.nx_pydot.read_dot("graph.dot")

    dmtr = nx.diameter(nx_graph)
    radius = nx.radius(nx_graph)

    print("D(G)=%d" % dmtr)
    print("R(G)=%d" % radius)

    graph.add_node("D(G)=%d" % dmtr, color='invis', width=0.8)
    graph.add_node("R(G)=%d" % radius, color='invis', width=0.8)

    if diameter:
        path_graph = color_diameter(graph, nx_graph, dmtr)
        graph = path_graph

    if draw:
        graph.draw("graph.pdf", prog='dot')
    return dmtr, radius


def write_graph(graph, style='dot'):
    """
    Create a Graphviz dot-file and a pdf-file of a graph
    prog=[‘neato’|’dot’|’twopi’|’circo’|’fdp’|’nop’]
    :param graph: A pygraphviz Agraph object
    :param style: A pygraphviz graph attribute
    """
    graph.write("graph.dot")
    graph.draw("graph.pdf", prog=style)


if __name__ == '__main__':
    # Commandline parsing
    log_levels = ['debug', 'info', 'warning', 'error']

    # get pretty print names for the search algorithms:
    # use the function/class name and strip off '_search'
    def get_callable_names(callables, omit_string):
        names = [c.__name__ for c in callables]
        names = [n.replace(omit_string, '').replace('_', ' ') for n in names]
        return ', '.join(names)

    argparser = argparse.ArgumentParser(
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='domain', nargs='?')
    argparser.add_argument(dest='problem')
    argparser.add_argument('-l', '--loglevel', choices=log_levels,
                           default='info')
    argparser.add_argument('-g', '--graphtype', choices=['relatedness', 'causal', 'rel_simple'],
                           default='relatedness')
    argparser.add_argument('--grounding', choices=['new', 'original'], default='original')
    argparser.add_argument('-d', '--diameter', choices=['true', 'false'], default='true')
    args = argparser.parse_args()

    if args.grounding == 'new':
        import grounding_new as grounding
    elif args.grounding == 'original':
        import grounding_orig as grounding


    logging.basicConfig(level=getattr(logging, args.loglevel.upper()),
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    stream=sys.stdout)

    args.problem = os.path.abspath(args.problem)
    if args.domain is None:
        args.domain = find_domain(args.problem)
    else:
        args.domain = os.path.abspath(args.domain)

    problem = parse(args.domain, args.problem)
    task = ground(problem)

    if args.graphtype == 'relatedness' and args.diameter == 'true':
        build_graph_related(task, static=True, draw=True, diameter=True)
    elif args.graphtype == 'relatedness' and args.diameter == 'false':
        build_graph_related(task, static=True, draw=True, diameter=False)
    elif args.graphtype == 'rel_simple':
        if args.grounding == 'original':
            raise Exception('The simple relatedness graph is only available with the new grounding')
        parser = Parser(args.domain, args.problem)
        domain = parser.parse_domain(args.domain)
        if args.diameter == 'true':
            build_graph_rel_simple(domain, task, draw=True)
        elif args.diameter == 'false':
            build_graph_rel_simple(domain, task, draw=True, diameter=False)
    elif args.graphtype == 'causal':
        build_graph_causal(task)
