/* Controles de rutas sobre el mapa original. La capa independiente conserva
   el camino completo al explorar vecinos, buscar ciudades o filtrar estados. */
'use strict';
const routeGraph = new RouteSearch.Graph(G);
const originInput = document.getElementById('origin');
const destinationInput = document.getElementById('destination');
const routeStatus = document.getElementById('route-status');
const routeLayer = document.createElementNS(NS, 'g');
routeLayer.id = 'route-layer';
world.appendChild(routeLayer);
let currentRoute = null;

function cityLabel(n) { return `${n.name} — ${n.state} [id=${n.id}]`; }
const fullLabels = new Map();
const cityOptions = document.getElementById('city-options');
for (const n of [...G.nodes].sort((a, b) => a.name.localeCompare(b.name, 'es') || a.id - b.id)) {
  const label = cityLabel(n), option = document.createElement('option');
  fullLabels.set(label, n.id);
  option.value = label;
  cityOptions.appendChild(option);
}
function resolveInput(value) {
  value = value.trim();
  if (fullLabels.has(value)) return fullLabels.get(value);
  if (/^id:\d+$/.test(value) && routeGraph.nodes.has(Number(value.slice(3)))) return Number(value.slice(3));
  const matches = G.nodes.filter(n => n.name === value);
  if (matches.length === 1) return matches[0].id;
  if (matches.length > 1) throw new Error(`Nombre ambiguo: ${value}. Elige una opción con estado e ID: ${matches.map(cityLabel).join('; ')}.`);
  throw new Error(`No se encontró «${value}». Selecciona una sugerencia; los acentos importan.`);
}
function routeElement(tag, attrs, text) {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  routeLayer.appendChild(el);
  return el;
}
function clearRoute() {
  currentRoute = null;
  routeLayer.replaceChildren();
  document.getElementById('route-result').hidden = true;
  document.getElementById('map-caption').textContent = 'Explora el grafo o calcula una ruta';
  routeStatus.textContent = '';
  nodeLayer.style.opacity = '';
  edgeLayer.style.opacity = '';
  labelLayer.style.opacity = '';
}
function fitRoute() {
  if (!currentRoute) { panX = panY = 0; zoom = 1; applyView(); return; }
  const points = currentRoute.path.map(id => routeGraph.nodes.get(id)).map(n => project(n.lon, n.lat));
  const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  zoom = Math.min(3, (W - 160) / Math.max(1, x1 - x0), (H - 180) / Math.max(1, y1 - y0));
  panX = W / 2 - (x0 + x1) / 2 * zoom;
  panY = H / 2 - (y0 + y1) / 2 * zoom;
  applyView();
}
function displayRoute(result) {
  currentRoute = result;
  routeLayer.replaceChildren();
  nodeLayer.style.opacity = '0.22';
  edgeLayer.style.opacity = '0.25';
  labelLayer.style.opacity = '0.2';
  const cities = result.path.map(id => routeGraph.nodes.get(id));
  const points = cities.map(n => project(n.lon, n.lat));
  for (let i = 1; i < points.length; i++) {
    const [a, b] = [points[i - 1], points[i]];
    routeElement('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: '#1766b2',
      'stroke-width': 3.5, 'stroke-linecap': 'round', 'vector-effect': 'non-scaling-stroke',
      'data-from': cities[i - 1].id, 'data-to': cities[i].id });
  }
  points.forEach((p, i) => {
    const endpoint = i === 0 || i === points.length - 1;
    const circle = routeElement('circle', { cx: p[0], cy: p[1], r: endpoint ? 6 : 2.4,
      fill: i === 0 ? '#167351' : i === points.length - 1 ? '#c54d23' : '#1766b2',
      stroke: '#fff', 'stroke-width': endpoint ? 1.6 : 0.7, 'data-id': cities[i].id });
    const title = document.createElementNS(NS, 'title');
    title.textContent = `${i}. ${cityLabel(cities[i])}`;
    circle.appendChild(title);
  });
  for (const i of [...new Set([0, points.length - 1])]) {
    const p = points[i], right = p[0] > W - 140;
    routeElement('text', { x: p[0] + (right ? -10 : 10), y: p[1] - 12, class: 'lbl',
      'text-anchor': right ? 'end' : 'start', style: 'font-size:14px' }, cities[i].name);
  }
  document.getElementById('route-result').hidden = false;
  document.getElementById('route-cost').textContent = result.cost.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' km';
  document.getElementById('route-metrics').textContent = `${result.depth} saltos · ${result.expanded} nodos expandidos`;
  document.getElementById('route-heuristic').textContent = `h = haversine × ${result.heuristic_scale.toFixed(9)}`;
  document.getElementById('path-count').textContent = `Ver recorrido completo (${cities.length} ciudades)`;
  const list = document.getElementById('route-path');
  list.replaceChildren();
  cities.forEach(n => { const item = document.createElement('li'); item.textContent = cityLabel(n); list.appendChild(item); });
  document.getElementById('map-caption').textContent = `${cities[0].name} → ${cities.at(-1).name}`;
  routeStatus.textContent = 'SUCCESS · Ruta mínima encontrada';
  fitRoute();
}
function calculateRoute(event) {
  if (event) event.preventDefault();
  if (!originInput.reportValidity() || !destinationInput.reportValidity()) return;
  clearRoute();
  try {
    const start = resolveInput(originInput.value), goal = resolveInput(destinationInput.value);
    originInput.value = cityLabel(routeGraph.nodes.get(start));
    destinationInput.value = cityLabel(routeGraph.nodes.get(goal));
    const result = routeGraph.search(start, goal);
    if (result.status !== 'SUCCESS') throw new Error('No existe un camino entre las ciudades seleccionadas.');
    displayRoute(result);
  } catch (error) { routeStatus.textContent = 'ERROR · ' + error.message; }
}
// No hay envío de formulario ni navegación: clic y Enter calculan localmente.
document.getElementById('calculate-route').addEventListener('click', calculateRoute);
for (const input of [originInput, destinationInput]) {
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.isComposing) calculateRoute(event);
  });
}
originInput.addEventListener('input', clearRoute);
destinationInput.addEventListener('input', clearRoute);
document.getElementById('swap-route').addEventListener('click', () => {
  [originInput.value, destinationInput.value] = [destinationInput.value, originInput.value];
  clearRoute();
});
document.getElementById('clear-route').addEventListener('click', () => { clearRoute(); fitRoute(); });
document.getElementById('fit-route').addEventListener('click', fitRoute);
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  [originInput.value, destinationInput.value] = button.dataset.example.split('|');
  calculateRoute();
}));
