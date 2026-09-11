"""CLI: python find_route.py --from-city Tijuana --to Cancún"""
import argparse
import json
from pathlib import Path
from route_search import Graph, RouteFindingProblem, a_star_search


def main():
    parser = argparse.ArgumentParser(description='Rutas mínimas con A* en el grafo de México.')
    parser.add_argument('--from-city', required=True, help='Nombre exacto o id:N')
    parser.add_argument('--to', required=True, help='Nombre exacto o id:N')
    parser.add_argument('--from-state', help='Estado exacto del origen')
    parser.add_argument('--to-state', help='Estado exacto del destino')
    parser.add_argument('--graph', type=Path, default=Path(__file__).with_name('mexico_cities_graph.json'))
    parser.add_argument('--ucs', action='store_true', help='Comparación opcional: h = 0')
    parser.add_argument('--json', action='store_true', help='Salida estructurada con ruta completa')
    args = parser.parse_args()
    try:
        graph = Graph.load(args.graph)
        start = graph.resolve(args.from_city, args.from_state)
        goal = graph.resolve(args.to, args.to_state)
        result = a_star_search(RouteFindingProblem(graph, start, goal), ucs=args.ucs)
    except (ValueError, OSError) as error:
        parser.exit(2, f'Status: ERROR\n{error}\n')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {result['status']}")
        print(f'From: {graph.label(start)}')
        print(f'To: {graph.label(goal)}')
        print('Path: ' + ' -> '.join(graph.label(i) for i in result['path']))
        print(f"Depth (hops): {result['depth']}")
        print(f"Cost (km): {result['cost']:.2f}" if result['cost'] is not None else 'Cost (km): N/A')
        print(f"Expanded: {result['expanded']}")
        print(f"Heuristic: {result['heuristic']}; alpha={result['heuristic_scale']:.12f}")
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
