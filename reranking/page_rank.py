#!/usr/bin/python
# Author: Nuttapon Thanitsukkan 5710501565

import numpy as np
from fractions import Fraction

def float_format(vector, decimal):
    return np.round((vector).astype(np.float), decimals=decimal)

def ranking(webgraphs, beta=0.85, eps=5e-10):
    dimension = len(webgraphs)
    dp = Fraction(1, dimension)
    M = np.zeros((dimension, dimension))
    E = np.zeros((dimension, dimension))
    E[:] = dp
    for index, graph in enumerate(webgraphs):
        graph = graph.split(',')
        num = len(graph)
        if graph[0] == '-':
            M[index] = dp
        else:
            for v in graph:
                dpp = Fraction(1, num)
                M[index, int(v) - 1] = dpp
    A = beta * M + ((1 - beta) * E)
    x = np.matrix([dp] * dimension)
    x = np.transpose(x)
    A = np.transpose(A)
    previous_x = x
    while True:
        x = A * x
        if np.linalg.norm(previous_x - x) < eps:
            break
        previous_x = x
    print "Final:\n", float_format(x, 8)
    with open('PageRank.txt', 'wb') as f:
        for rank in float_format(x, 8):
            f.write(str(rank[0]) + '\n')
    print "sum", np.sum(x)
                

if __name__ == '__main__':
    with open('webgraph.txt') as f:
        webgraphs = f.read().split('\n')[:-1]
    ranking(webgraphs)
