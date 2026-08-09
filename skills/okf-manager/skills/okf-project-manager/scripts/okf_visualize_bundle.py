#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[A-Za-z0-9_-]*)?\)")
_TYPE_COLORS = [
    "#60a5fa",
    "#34d399",
    "#f59e0b",
    "#f472b6",
    "#a78bfa",
    "#22d3ee",
    "#fb7185",
    "#84cc16",
]



def _is_raw_evidence(rel) -> bool:
    parts = rel.parts if hasattr(rel, "parts") else Path(str(rel)).parts
    return len(parts) >= 2 and parts[0] == "sources" and parts[1] == "raw"

def _build_graph(root: Path) -> dict:
    concepts = []
    ids = set()
    bodies = {}
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        rel = md.relative_to(root)
        if _is_raw_evidence(rel):
            continue
        cid = rel.with_suffix("").as_posix()
        ids.add(cid)
        fm, body = _doc(md)
        tags = fm.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        node = {
            "id": cid,
            "type": str(fm.get("type") or "Unknown"),
            "title": str(fm.get("title") or cid),
            "description": str(fm.get("description") or ""),
            "resource": str(fm.get("resource") or ""),
            "tags": [str(t) for t in tags],
            "path": rel.as_posix(),
            "body": body,
        }
        concepts.append(node)
        bodies[cid] = body

    edges = []
    seen = set()
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        rel = md.relative_to(root)
        if _is_raw_evidence(rel):
            continue
        source = rel.with_suffix("").as_posix()
        _, body = _doc(md)
        for m in _LINK_RE.finditer(body):
            target = m.group(1)
            if "://" in target or target.startswith("/"):
                continue
            try:
                dest = (md.parent / target).resolve().relative_to(root.resolve()).with_suffix("").as_posix()
            except Exception:
                continue
            if dest in ids and dest != source and (source, dest) not in seen:
                seen.add((source, dest))
                edges.append({"source": source, "target": dest})

    type_names = sorted({n["type"] for n in concepts})
    palette = {typ: _TYPE_COLORS[i % len(_TYPE_COLORS)] for i, typ in enumerate(type_names)}
    return {
        "mode": "live-d3-self-graph",
        "nodes": concepts,
        "edges": edges,
        "types": type_names,
        "palette": palette,
        "stats": {
            "mode": "live-d3-self-graph",
            "concepts": len(concepts),
            "edges": len(edges),
            "types": len(type_names),
        },
    }



def _parse_simple_frontmatter(raw: str) -> dict:
    """Parse the simple YAML subset commonly used by OKF frontmatter.

    This fallback keeps the standalone helper script independent of PyYAML so
    `./scripts/okf_visualize_bundle.py` works under the system Python too.
    """
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [item.strip().strip('"\'') for item in inner.split(",") if item.strip()]
        else:
            result[key] = value.strip('"\'')
    return result


def _load_frontmatter(raw: str) -> dict:
    try:
        import yaml

        parsed = yaml.safe_load(raw) or {}
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return _parse_simple_frontmatter(raw)


def _doc(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    normalized = text.replace("\r\n", "\n")
    if normalized.startswith("---\n"):
        end = normalized.find("\n---", 4)
        if end >= 0:
            fm = _load_frontmatter(normalized[4:end])
            body = normalized[end + 4 :].lstrip("\n")
            return fm, body
    return {}, normalized

def _render_html(bundle_name: str, graph: dict) -> str:
    data = json.dumps(graph, ensure_ascii=False)
    title = html.escape(bundle_name)
    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OKF Live Self-Graph — __TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
:root { color-scheme: dark; --bg:#0f172a; --panel:#111827; --muted:#94a3b8; --text:#e5e7eb; --accent:#38bdf8; --line:#334155; }
* { box-sizing: border-box; }
html, body { width:100%; height:100%; margin:0; overflow:hidden; }
body { font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; background:var(--bg); color:var(--text); }
header { height:58px; display:flex; align-items:center; gap:16px; padding:10px 16px; border-bottom:1px solid var(--line); background:#020617; overflow:hidden; }
header h1 { margin:0; font-size:18px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
header .stats { color:var(--muted); font-size:13px; white-space:nowrap; }
main { --left-panel-width:280px; --right-panel-width:360px; display:grid; grid-template-columns: var(--left-panel-width) 7px minmax(0, 1fr) 7px var(--right-panel-width); height:calc(100vh - 58px); min-height:0; overflow:hidden; }
aside, section { min-height:0; min-width:0; }
.sidebar, .detail { background:var(--panel); border-right:1px solid var(--line); overflow:auto; padding:14px; }
.detail { display:flex; flex-direction:column; min-height:0; }
.detail { border-right:0; border-left:1px solid var(--line); }
.resizer { background:#020617; border-left:1px solid var(--line); border-right:1px solid var(--line); cursor:col-resize; min-width:7px; touch-action:none; z-index:6; }
.resizer:hover, .resizer.dragging { background:#0f3b57; border-color:var(--accent); }
.graph-wrap { position:relative; min-width:0; min-height:0; overflow:hidden; contain:layout paint; }
#graph { width:100%; height:100%; display:block; background:radial-gradient(circle at 50% 40%, #172554 0%, #0f172a 48%, #020617 100%); touch-action:none; }
input, select, button { width:100%; border:1px solid #334155; border-radius:8px; background:#020617; color:var(--text); padding:8px 10px; margin:6px 0 12px; }
button { cursor:pointer; background:#0f172a; }
button:hover { border-color:var(--accent); }
.legend-item { display:flex; align-items:center; gap:8px; margin:6px 0; color:#cbd5e1; }
.swatch { width:11px; height:11px; border-radius:50%; flex:none; }
.node-list { margin-top:12px; border-top:1px solid var(--line); padding-top:8px; }
.custom-select { position:relative; margin:6px 0 12px; }
.type-summary { width:100%; border:1px solid #334155; border-radius:8px; background:#020617; color:var(--text); padding:8px 10px; cursor:pointer; list-style:none; }
.type-summary::-webkit-details-marker { display:none; }
.type-summary::after { content:'▾'; float:right; color:var(--muted); }
.custom-select[open] .type-summary { border-color:var(--accent); }
.type-menu { position:absolute; left:0; right:0; top:calc(100% + 4px); max-height:min(360px, 60vh); overflow:auto; border:1px solid #334155; border-radius:8px; background:#020617; margin-top:0; padding:4px; box-shadow:0 12px 28px rgba(0,0,0,.55); z-index:30; }
.type-option { width:100%; text-align:left; border:0; border-radius:6px; margin:2px 0; padding:7px 8px; background:transparent; color:#cbd5e1; }
.type-option:hover, .type-option.active { background:#1e293b; color:white; }
.native-type-select { display:none; }
.node-row { padding:7px; border-radius:7px; cursor:pointer; color:#cbd5e1; }
.node-row:hover, .node-row.active { background:#1e293b; color:white; }
.badge { display:inline-block; padding:2px 6px; border:1px solid #334155; border-radius:999px; color:#cbd5e1; font-size:11px; margin:2px 4px 2px 0; }
.detail h2 { margin:0 0 4px; font-size:19px; }
.detail .id { color:var(--muted); font-family:ui-monospace,monospace; font-size:12px; word-break:break-all; }
.detail pre { white-space:pre-wrap; background:#020617; padding:10px; border-radius:8px; overflow:auto; border:1px solid #334155; }
.detail .body-preview { flex:1 1 auto; min-height:180px; max-height:none; margin-bottom:0; }
.detail a { color:#7dd3fc; }
.empty { color:var(--muted); }
.toolbar { position:absolute; top:12px; right:12px; display:flex; gap:8px; z-index:4; }
.toolbar button { width:auto; margin:0; opacity:.92; }
.tooltip { position:fixed; pointer-events:none; background:#020617; border:1px solid #334155; padding:6px 8px; border-radius:7px; color:#e5e7eb; max-width:min(300px, 70vw); display:none; z-index:20; will-change:transform; }
.node circle { cursor:pointer; stroke:#020617; stroke-width:1.5px; }
.node.selected circle { stroke:#fff; stroke-width:4px; }
.node.hover circle { stroke:#bae6fd; stroke-width:3px; }
.node text { pointer-events:none; fill:#e5e7eb; font-size:12px; paint-order:stroke; stroke:#020617; stroke-width:3px; stroke-linejoin:round; }
.link { stroke:rgba(148,163,184,.5); stroke-width:1.2px; marker-end:url(#arrow); }
.link.selected { stroke:#7dd3fc; stroke-width:1.8px; marker-end:url(#arrow-selected); }
@media (max-width: 1000px) { main { --left-panel-width:240px; grid-template-columns: var(--left-panel-width) 7px minmax(0, 1fr); } .right-resizer { display:none; } .detail { position:absolute; right:0; top:58px; bottom:0; width:min(var(--right-panel-width), 90vw); z-index:5; } }
</style>
</head>
<body>
<header>
  <h1>OKF Live Self-Graph — __TITLE__</h1>
  <div class="stats" id="stats"></div>
</header>
<main>
  <aside class="sidebar">
    <label>Search concepts</label>
    <input id="search" placeholder="title, id, tag, description">
    <label>Filter by type</label>
    <select id="typeFilter" class="native-type-select" aria-hidden="true"><option value="">All types</option></select>
    <details id="typeDropdown" class="custom-select">
      <summary id="typeSummary" class="type-summary">All types</summary>
      <div id="typeMenu" class="type-menu" role="listbox" aria-label="Filter by type"></div>
    </details>
    <button id="fitBtn">Fit graph</button>
    <button id="pinBtn">Unpin all nodes</button>
    <p class="empty">Live D3 self-graph: nodes are draggable and pinnable. Double-click a node to unpin it; use the mouse wheel to zoom and drag empty space to pan.</p>
    <h3>Types</h3>
    <div id="legend"></div>
    <div class="node-list" id="nodeList"></div>
  </aside>
  <div class="resizer left-resizer" id="leftResizer" title="Resize left panel" aria-label="Resize left panel"></div>
  <section class="graph-wrap" id="graphWrap">
    <svg id="graph" role="img" aria-label="OKF knowledge graph" preserveAspectRatio="xMidYMid meet"></svg>
    <div class="toolbar"><button id="zoomIn">+</button><button id="zoomOut">−</button><button id="resetZoom">Reset</button></div>
    <div class="tooltip" id="tooltip"></div>
  </section>
  <div class="resizer right-resizer" id="rightResizer" title="Resize right panel" aria-label="Resize right panel"></div>
  <aside class="detail" id="detail"><p class="empty">Select a concept node to inspect frontmatter, body preview, outgoing links, and backlinks.</p></aside>
</main>
<script id="bundle-data" type="application/json">__GRAPH_DATA__</script>
<script>
(() => {
if (!window.d3) {
  document.getElementById('detail').innerHTML = '<p class="empty"><strong>D3 failed to load.</strong> Check network access to https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js and reload this page.</p>';
  return;
}
const bundle = JSON.parse(document.getElementById('bundle-data').textContent);
const palette = bundle.palette || {};
const nodes = bundle.nodes.map((n, i) => ({...n, idx:i, visible:true, r:9 + Math.min(18, Math.sqrt((n.body||'').length)/9)}));
const byId = new Map(nodes.map(n => [n.id, n]));
const links = bundle.edges.map(e => ({source:e.source, target:e.target}));
const svg = d3.select('#graph');
const wrap = document.getElementById('graphWrap');
const tooltip = document.getElementById('tooltip');
const root = svg.append('g').attr('class','root');
const linkLayer = root.append('g').attr('class','links');
const nodeLayer = root.append('g').attr('class','nodes');
let selected = null, width = 1, height = 1, resizeTimer = null;

const defs = svg.append('defs');
defs.append('marker').attr('id','arrow').attr('viewBox','0 -5 10 10').attr('refX',18).attr('refY',0).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto').append('path').attr('d','M0,-5L10,0L0,5').attr('fill','rgba(148,163,184,.7)');
defs.append('marker').attr('id','arrow-selected').attr('viewBox','0 -5 10 10').attr('refX',18).attr('refY',0).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto').append('path').attr('d','M0,-5L10,0L0,5').attr('fill','#7dd3fc');

const zoom = d3.zoom().scaleExtent([0.1, 5]).on('zoom', event => root.attr('transform', event.transform));
svg.call(zoom);

const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(125).strength(0.35))
  .force('charge', d3.forceManyBody().strength(-420))
  .force('collide', d3.forceCollide().radius(d => d.r + 8).iterations(2))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('x', d3.forceX(width / 2).strength(0.035))
  .force('y', d3.forceY(height / 2).strength(0.035))
  .on('tick', ticked);

let linkSel = linkLayer.selectAll('line');
let nodeSel = nodeLayer.selectAll('g.node');

function escape(s) { return String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function visibleNodes() { return nodes.filter(n => n.visible); }
function visibleLinks() { return links.filter(e => e.source.visible && e.target.visible); }
function linkTouchesSelection(d) { return selected && (d.source === selected || d.target === selected); }

function renderGraph() {
  linkSel = linkLayer.selectAll('line').data(visibleLinks(), d => d.source.id + '→' + d.target.id).join('line').attr('class', d => 'link' + (linkTouchesSelection(d) ? ' selected' : ''));
  nodeSel = nodeLayer.selectAll('g.node').data(visibleNodes(), d => d.id).join(
    enter => {
      const g = enter.append('g').attr('class','node').call(dragBehavior());
      g.append('circle').attr('r', d => d.r).attr('fill', d => palette[d.type] || '#94a3b8');
      g.append('text').attr('x', d => d.r + 5).attr('y', 4).text(d => d.title || d.id);
      g.on('click', (event,d) => { event.stopPropagation(); select(d); })
       .on('mouseover', (event,d) => { d3.select(event.currentTarget).classed('hover', true); showTooltip(event, d); })
       .on('mousemove', (event,d) => showTooltip(event, d))
       .on('mouseout', (event,d) => { d3.select(event.currentTarget).classed('hover', false); hideTooltip(); })
       .on('dblclick', (event,d) => { event.stopPropagation(); d.fx = null; d.fy = null; });
      return g;
    },
    update => update,
    exit => exit.remove()
  );
  nodeSel.classed('selected', d => d === selected);
  simulation.nodes(visibleNodes());
  simulation.force('link').links(visibleLinks());
  simulation.alpha(0.35).restart();
  updateStats();
}

function ticked() {
  linkSel.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y)
         .attr('class', d => 'link' + (linkTouchesSelection(d) ? ' selected' : ''));
  nodeSel.attr('transform', d => `translate(${d.x},${d.y})`);
}

function dragBehavior() {
  return d3.drag()
    .on('start', (event,d) => { if (!event.active) simulation.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; })
    .on('drag', (event,d) => { d.fx = event.x; d.fy = event.y; })
    .on('end', (event,d) => { if (!event.active) simulation.alphaTarget(0); });
}

function showTooltip(event, d) {
  tooltip.style.display = 'block';
  tooltip.textContent = (d.title || d.id) + ' · ' + d.type;
  const pad = 14, tw = tooltip.offsetWidth || 220, th = tooltip.offsetHeight || 32;
  const left = Math.min(window.innerWidth - tw - pad, Math.max(pad, event.clientX + 12));
  const top = Math.min(window.innerHeight - th - pad, Math.max(pad, event.clientY + 12));
  tooltip.style.transform = `translate(${left}px, ${top}px)`;
}
function hideTooltip() { tooltip.style.display = 'none'; }

function fit(duration=250) {
  const vs = visibleNodes();
  if (!vs.length) return;
  const bounds = root.node().getBBox();
  const dx = Math.max(1, bounds.width), dy = Math.max(1, bounds.height);
  const x = bounds.x + dx / 2, y = bounds.y + dy / 2;
  const k = Math.max(0.12, Math.min(2.8, 0.86 / Math.max(dx / width, dy / height)));
  const t = d3.zoomIdentity.translate(width / 2, height / 2).scale(k).translate(-x, -y);
  svg.transition().duration(duration).call(zoom.transform, t);
}

function resize() {
  const r = wrap.getBoundingClientRect();
  const nextW = Math.max(1, Math.round(r.width));
  const nextH = Math.max(1, Math.round(r.height));
  if (nextW === width && nextH === height) return;
  width = nextW; height = nextH;
  svg.attr('viewBox', `0 0 ${width} ${height}`);
  simulation.force('center', d3.forceCenter(width / 2, height / 2));
  simulation.force('x', d3.forceX(width / 2).strength(0.035));
  simulation.force('y', d3.forceY(height / 2).strength(0.035));
  simulation.alpha(0.2).restart();
}
function scheduleResize() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { resize(); fit(0); }, 120);
}

function currentTypeFilter() { return document.getElementById('typeFilter').value || ''; }
function setTypeFilter(value) {
  const select = document.getElementById('typeFilter');
  const summary = document.getElementById('typeSummary');
  const dropdown = document.getElementById('typeDropdown');
  select.value = value || '';
  summary.textContent = value || 'All types';
  document.querySelectorAll('.type-option').forEach(btn => btn.classList.toggle('active', btn.dataset.value === select.value));
  if (dropdown) dropdown.open = false;
  applyFilters();
}
function applyFilters() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const typ = currentTypeFilter();
  for (const n of nodes) {
    const hay = [n.id,n.title,n.description,n.type,(n.tags||[]).join(' ')].join(' ').toLowerCase();
    n.visible = (!q || hay.includes(q)) && (!typ || n.type === typ);
  }
  if (selected && !selected.visible) select(null);
  renderList(); renderGraph(); setTimeout(() => fit(150), 60);
}

function select(n) { selected = n; renderDetail(); renderList(); renderGraph(); }
function renderDetail() {
  const el = document.getElementById('detail');
  if (!selected) { el.innerHTML = '<p class="empty">Select a concept node to inspect frontmatter, body preview, outgoing links, and backlinks.</p>'; return; }
  const outgoing = links.filter(e => e.source === selected).map(e => e.target);
  const incoming = links.filter(e => e.target === selected).map(e => e.source);
  el.innerHTML = `<h2>${escape(selected.title)}</h2><div class="id">${escape(selected.id)}</div><p>${escape(selected.description)}</p><p><span class="badge">${escape(selected.type)}</span>${(selected.tags||[]).map(t=>`<span class="badge">${escape(t)}</span>`).join('')}</p>${selected.resource?`<p><strong>Resource:</strong><br><span class="id">${escape(selected.resource)}</span></p>`:''}<h3>Outgoing links</h3>${outgoing.length?'<ul>'+outgoing.map(n=>`<li><a href="#" data-id="${escape(n.id)}">${escape(n.title||n.id)}</a></li>`).join('')+'</ul>':'<p class="empty">None</p>'}<h3>Backlinks</h3>${incoming.length?'<ul>'+incoming.map(n=>`<li><a href="#" data-id="${escape(n.id)}">${escape(n.title||n.id)}</a></li>`).join('')+'</ul>':'<p class="empty">None</p>'}<h3>Body preview</h3><pre class="body-preview">${escape((selected.body||'').slice(0,2500))}</pre>`;
  el.querySelectorAll('a[data-id]').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); const n = byId.get(a.dataset.id); if (n) select(n); }));
}
function renderList() {
  const el = document.getElementById('nodeList'); const vs = visibleNodes();
  el.innerHTML = `<strong>${vs.length} visible concepts</strong>` + vs.slice(0,300).map(n=>`<div class="node-row ${n===selected?'active':''}" data-id="${escape(n.id)}">${escape(n.title||n.id)}<br><small>${escape(n.type)}</small></div>`).join('');
  el.querySelectorAll('.node-row').forEach(row => row.addEventListener('click', () => { const n = byId.get(row.dataset.id); if (n) select(n); }));
}
function updateStats() { document.getElementById('stats').textContent = `${visibleNodes().length}/${nodes.length} concepts · ${visibleLinks().length}/${links.length} links · ${bundle.types.length} types`; }
function initPanelResizers() {
  const main = document.querySelector('main');
  const left = document.getElementById('leftResizer');
  const right = document.getElementById('rightResizer');
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const startDrag = (event, side) => {
    event.preventDefault();
    const handle = side === 'left' ? left : right;
    handle.classList.add('dragging');
    const move = ev => {
      const rect = main.getBoundingClientRect();
      if (side === 'left') {
        const rightWidth = parseFloat(getComputedStyle(main).getPropertyValue('--right-panel-width')) || 360;
        const w = clamp(ev.clientX - rect.left, 120, Math.max(120, rect.width - rightWidth - 14));
        main.style.setProperty('--left-panel-width', `${Math.round(w)}px`);
      } else {
        const leftWidth = parseFloat(getComputedStyle(main).getPropertyValue('--left-panel-width')) || 280;
        const w = clamp(rect.right - ev.clientX, 120, Math.max(120, rect.width - leftWidth - 14));
        main.style.setProperty('--right-panel-width', `${Math.round(w)}px`);
      }
      scheduleResize();
    };
    const up = () => {
      handle.classList.remove('dragging');
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      scheduleResize();
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  if (left) left.addEventListener('pointerdown', ev => startDrag(ev, 'left'));
  if (right) right.addEventListener('pointerdown', ev => startDrag(ev, 'right'));
}

function initUi() {
  const typeFilter = document.getElementById('typeFilter');
  const typeMenu = document.getElementById('typeMenu');
  for (const t of bundle.types) typeFilter.insertAdjacentHTML('beforeend', `<option value="${escape(t)}">${escape(t)}</option>`);
  const typeChoices = [''].concat(bundle.types);
  typeMenu.innerHTML = typeChoices.map(t => `<button type="button" class="type-option ${t===''?'active':''}" role="option" data-value="${escape(t)}">${escape(t || 'All types')}</button>`).join('');
  typeMenu.querySelectorAll('.type-option').forEach(btn => btn.addEventListener('click', ev => { ev.preventDefault(); setTypeFilter(btn.dataset.value || ''); }));
  document.getElementById('legend').innerHTML = bundle.types.map(t=>`<div class="legend-item"><span class="swatch" style="background:${palette[t]||'#94a3b8'}"></span>${escape(t)}</div>`).join('');
  document.getElementById('search').addEventListener('input', applyFilters);
  typeFilter.addEventListener('change', () => setTypeFilter(typeFilter.value));
  document.getElementById('fitBtn').onclick = () => fit();
  document.getElementById('pinBtn').onclick = () => { nodes.forEach(n => { n.fx = null; n.fy = null; }); simulation.alpha(0.25).restart(); };
  document.getElementById('zoomIn').onclick = () => svg.transition().duration(160).call(zoom.scaleBy, 1.2);
  document.getElementById('zoomOut').onclick = () => svg.transition().duration(160).call(zoom.scaleBy, 0.83);
  document.getElementById('resetZoom').onclick = () => fit();
  svg.on('click', () => select(null));
}

initUi(); initPanelResizers(); resize(); renderList(); renderGraph(); setTimeout(() => fit(0), 250);
if ('ResizeObserver' in window) new ResizeObserver(scheduleResize).observe(wrap); else window.addEventListener('resize', scheduleResize);
})();
</script>
</body>
</html>
"""
    return template.replace("__TITLE__", title).replace("__GRAPH_DATA__", data.replace("</", "<\\/"))



def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print("Usage: okf_visualize_bundle.py <bundle_root> [out_html]")
        return 2
    root = Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"Bundle directory not found: {root}", file=sys.stderr)
        return 1
    out = Path(argv[2]).expanduser().resolve() if len(argv) > 2 else root / "viz.html"
    graph = _build_graph(root)
    page = _render_html(root.name, graph)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if '<script id="bundle-data" type="application/json">' not in page or '<svg id="graph"' not in page:
        print("Generated visualization missing required live D3 self-graph elements", file=sys.stderr)
        return 1
    print(json.dumps({
        "concepts": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "path": str(out),
        "bytes": len(page.encode("utf-8")),
        "mode": "live-d3-self-graph",
        "d3": "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
