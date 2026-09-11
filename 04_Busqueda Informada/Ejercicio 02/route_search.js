/* Puerto de route_search.py; A* adaptado de
   Búsqueda informada/project/search/astar.py. Sin librerías ni red. */
(function (root) {
  'use strict';
  function haversine(a, b) {
    const rad = n => n * Math.PI / 180;
    const p1 = rad(a.lat), p2 = rad(b.lat);
    const dphi = rad(b.lat - a.lat), dlmb = rad(b.lon - a.lon);
    const v = Math.sin(dphi / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dlmb / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, v))));
  }
  class MinHeap {
    constructor() { this.items = []; }
    less(a, b) { return a.f < b.f || (a.f === b.f && a.order < b.order); }
    push(item) {
      const a = this.items;
      a.push(item);
      let i = a.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (!this.less(a[i], a[p])) break;
        [a[i], a[p]] = [a[p], a[i]]; i = p;
      }
    }
    pop() {
      const a = this.items, first = a[0], last = a.pop();
      if (a.length) {
        a[0] = last;
        let i = 0;
        while (true) {
          let best = i, l = 2 * i + 1, r = l + 1;
          if (l < a.length && this.less(a[l], a[best])) best = l;
          if (r < a.length && this.less(a[r], a[best])) best = r;
          if (best === i) break;
          [a[i], a[best]] = [a[best], a[i]]; i = best;
        }
      }
      return first;
    }
  }
  class Graph {
    constructor(payload) {
      this.nodes = new Map(payload.nodes.map(n => [n.id, n]));
      this.adj = new Map(payload.nodes.map(n => [n.id, new Map()]));
      this.scale = 1;
      for (const e of payload.edges) {
        if (!Number.isFinite(e.km) || e.km < 0) throw new Error('Costo inválido.');
        this.adj.get(e.source).set(e.target, e.km);
        this.adj.get(e.target).set(e.source, e.km);
        const d = haversine(this.nodes.get(e.source), this.nodes.get(e.target));
        if (d) this.scale = Math.min(this.scale, e.km / d);
      }
      this.scale *= 1 - 1e-12;
    }
    search(start, goal, ucs = false) {
      if (!this.nodes.has(start) || !this.nodes.has(goal)) throw new Error('Ciudad desconocida.');
      const h = id => ucs ? 0 : this.scale * haversine(this.nodes.get(id), this.nodes.get(goal));
      const frontier = new MinHeap(), bestG = new Map([[start, 0]]);
      let order = 0, expanded = 0;
      frontier.push({ id: start, g: 0, f: h(start), order: 0, parent: null });
      while (frontier.items.length) {
        const node = frontier.pop();
        if (node.g !== bestG.get(node.id)) continue;
        if (node.id === goal) {
          const path = [];
          for (let n = node; n; n = n.parent) path.push(n.id);
          path.reverse();
          return { status: 'SUCCESS', path, depth: path.length - 1, cost: node.g, expanded,
            heuristic: ucs ? 'h = 0 (UCS)' : 'haversine al destino × alpha', heuristic_scale: this.scale };
        }
        expanded++;
        for (const [id, km] of this.adj.get(node.id)) {
          const g = node.g + km;
          if (g < (bestG.get(id) ?? Infinity)) {
            bestG.set(id, g);
            frontier.push({ id, g, f: g + h(id), order: ++order, parent: node });
          }
        }
      }
      return { status: 'FAILURE', path: [], depth: 0, cost: null, expanded,
        heuristic: ucs ? 'h = 0 (UCS)' : 'haversine al destino × alpha', heuristic_scale: this.scale };
    }
  }
  const api = { Graph, haversine };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RouteSearch = api;
})(globalThis);
