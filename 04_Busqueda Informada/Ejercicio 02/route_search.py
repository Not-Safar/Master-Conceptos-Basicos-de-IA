"""A* de México, adaptado del proyecto de Rumania del curso.

Origen: Búsqueda informada/project/search/astar.py y romania/{node,problem}.py.
Copias originales para consulta en referencia/. Sin dependencias externas.
"""
from __future__ import annotations

import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Adaptada de Mexico map/generate_mexico_graph.py; radio = 6371 km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


class Graph:
    def __init__(self, payload: dict):
        self.nodes = {n['id']: n for n in payload['nodes']}
        self.adj = {city: {} for city in self.nodes}
        self.heuristic_scale = 1.0
        for edge in payload['edges']:
            a, b, km = edge['source'], edge['target'], edge['km']
            if km < 0 or not math.isfinite(km):
                raise ValueError('Los costos deben ser finitos y no negativos.')
            self.adj[a][b] = km
            self.adj[b][a] = km
            distance = self.distance(a, b)
            if distance:
                self.heuristic_scale = min(self.heuristic_scale, km / distance)
        # Los km del JSON están redondeados. alpha*d(a,b) <= costo(a,b)
        # conserva consistencia sin cambiar ninguna arista ni su peso.
        self.heuristic_scale *= 1 - 1e-12

    @classmethod
    def load(cls, path: Path | str):
        return cls(json.loads(Path(path).read_text(encoding='utf-8')))

    def distance(self, a: int, b: int) -> float:
        a, b = self.nodes[a], self.nodes[b]
        return haversine(a['lat'], a['lon'], b['lat'], b['lon'])

    def label(self, city: int) -> str:
        n = self.nodes[city]
        return f"{n['name']}, {n['state']} [id={city}]"

    def resolve(self, name: str, state: str | None = None) -> int:
        """Acepta nombre exacto o id:123. Nunca elige un duplicado en silencio."""
        if name.startswith('id:'):
            try:
                city = int(name[3:])
            except ValueError:
                raise ValueError(f'ID inválido: {name}') from None
            matches = [city] if city in self.nodes else []
        else:
            matches = [i for i, n in self.nodes.items() if n['name'] == name]
        if state is not None:
            matches = [i for i in matches if self.nodes[i]['state'] == state]
        if not matches:
            raise ValueError(f'Ciudad no encontrada: {name!r}, estado={state!r}. Respeta acentos y espacios.')
        if len(matches) > 1:
            choices = '\n  '.join(self.label(i) for i in matches)
            raise ValueError(f'Nombre ambiguo: {name!r}. Indica --from-state / --to-state o usa id:N.\n  {choices}')
        return matches[0]


class RouteFindingProblem:
    def __init__(self, graph: Graph, start: int, goal: int):
        if start not in graph.nodes or goal not in graph.nodes:
            raise ValueError('El origen y destino deben pertenecer al grafo.')
        self.graph, self.start, self.goal = graph, start, goal

    def is_goal(self, state: int) -> bool:
        return state == self.goal


@dataclass
class Node:
    state: int
    parent: Node | None = None
    path_cost: float = 0.0
    depth: int = 0

    def path(self) -> list[int]:
        result, node = [], self
        while node is not None:
            result.append(node.state)
            node = node.parent
        return result[::-1]

    def expand(self, problem: RouteFindingProblem) -> list[Node]:
        return [Node(city, self, self.path_cost + km, self.depth + 1)
                for city, km in problem.graph.adj[self.state].items()]


def a_star_search(problem: RouteFindingProblem, *, ucs: bool = False) -> dict:
    """Frontera heap por (g+h, orden de inserción), como en Rumania.

    Descarta entradas obsoletas. Una mejora puede reabrir un estado.
    Expanded cuenta expansiones efectivas; no cuenta la prueba de meta.
    """
    graph = problem.graph
    def h(city):
        return 0.0 if ucs else graph.heuristic_scale * graph.distance(city, problem.goal)
    node = Node(problem.start)
    frontier = [(h(node.state), 0, node)]
    best_g = {node.state: 0.0}
    counter = expanded = 0
    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node.path_cost != best_g[node.state]:
            continue
        if problem.is_goal(node.state):
            return dict(status='SUCCESS', path=node.path(), depth=node.depth,
                        cost=node.path_cost, expanded=expanded,
                        heuristic='h = 0 (UCS)' if ucs else 'haversine al destino × alpha',
                        heuristic_scale=graph.heuristic_scale)
        expanded += 1
        for child in node.expand(problem):
            if child.path_cost < best_g.get(child.state, math.inf):
                best_g[child.state] = child.path_cost
                counter += 1
                heapq.heappush(frontier, (child.path_cost + h(child.state), counter, child))
    return dict(status='FAILURE', path=[], depth=0, cost=None, expanded=expanded,
                heuristic='h = 0 (UCS)' if ucs else 'haversine al destino × alpha',
                heuristic_scale=graph.heuristic_scale)
