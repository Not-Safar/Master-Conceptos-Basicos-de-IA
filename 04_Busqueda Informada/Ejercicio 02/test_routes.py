"""Verificación: python -m unittest -v test_routes.py"""
import heapq
import math
import random
import unittest
from pathlib import Path
from route_search import Graph, RouteFindingProblem, a_star_search


def distances_to(graph, goal):
    """Oráculo Dijkstra independiente: distancias desde el destino."""
    distances, heap = {goal: 0.0}, [(0.0, goal)]
    while heap:
        cost, city = heapq.heappop(heap)
        if cost > distances[city]:
            continue
        for neighbor, km in graph.adj[city].items():
            candidate = cost + km
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                heapq.heappush(heap, (candidate, neighbor))
    return distances


class RoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = Graph.load(Path(__file__).with_name('mexico_cities_graph.json'))

    def test_suggested_routes_optimal_and_valid(self):
        for start, goal in [('Tijuana', 'Cancún'), ('Mexico City', 'Monterrey'),
                            ('Guadalajara', 'Mérida'), ('Hermosillo', 'Oaxaca')]:
            with self.subTest(start=start, goal=goal):
                a, b = self.graph.resolve(start), self.graph.resolve(goal)
                result = a_star_search(RouteFindingProblem(self.graph, a, b))
                self.assertEqual(result['status'], 'SUCCESS')
                self.assertEqual(result['path'][0], a)
                self.assertEqual(result['path'][-1], b)
                self.assertEqual(result['depth'], len(result['path']) - 1)
                total = sum(self.graph.adj[x][y] for x, y in zip(result['path'], result['path'][1:]))
                self.assertAlmostEqual(total, result['cost'], places=8)
                self.assertAlmostEqual(distances_to(self.graph, b)[a], result['cost'], places=8)

    def test_random_sources_against_independent_oracle(self):
        starts = random.Random(42).sample(list(self.graph.nodes), 30)
        for goal in [self.graph.resolve('Cancún'), self.graph.resolve('Monterrey')]:
            distances = distances_to(self.graph, goal)
            self.assertEqual(len(distances), 1000)
            for start in starts:
                result = a_star_search(RouteFindingProblem(self.graph, start, goal))
                self.assertAlmostEqual(result['cost'], distances[start], places=8)

    def test_heuristic_consistent_with_rounded_costs(self):
        for name in ['Cancún', 'Monterrey', 'Mérida', 'Oaxaca']:
            goal = self.graph.resolve(name)
            h = {i: self.graph.heuristic_scale * self.graph.distance(i, goal) for i in self.graph.nodes}
            self.assertEqual(h[goal], 0)
            for a, neighbors in self.graph.adj.items():
                for b, km in neighbors.items():
                    self.assertLessEqual(h[a], km + h[b] + 1e-9)

    def test_same_city(self):
        result = a_star_search(RouteFindingProblem(self.graph, 6, 6))
        self.assertEqual((result['path'], result['cost'], result['depth'], result['expanded']), ([6], 0, 0, 0))

    def test_neighbors_both_directions(self):
        a = 6
        b = next(iter(self.graph.adj[a]))
        for start, goal in [(a, b), (b, a)]:
            result = a_star_search(RouteFindingProblem(self.graph, start, goal))
            self.assertAlmostEqual(result['cost'], distances_to(self.graph, goal)[start], places=8)

    def test_names_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, 'ambiguo'):
            self.graph.resolve('Puebla')
        city = self.graph.resolve('Puebla', 'Puebla')
        self.assertEqual(self.graph.resolve(f'id:{city}'), city)
        for text in ['Cancun', 'CDMX', 'id:100000', 'id:no']:
            with self.assertRaises(ValueError):
                self.graph.resolve(text)

    def test_disconnected_graph(self):
        graph = Graph({'nodes': [{'id': i, 'lat': 0, 'lon': i} for i in [10, 20]], 'edges': []})
        result = a_star_search(RouteFindingProblem(graph, 10, 20))
        self.assertEqual(result['status'], 'FAILURE')
        self.assertIsNone(result['cost'])


if __name__ == '__main__':
    unittest.main()
