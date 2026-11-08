#!/usr/bin/env node
// Structural signals for tour design: fan-in/out, entry points, BFS, non-code inventory, clusters.
const fs = require('fs');
const path = require('path');

const ENTRY_NAMES = new Set(['index.ts', 'index.js', 'main.ts', 'main.js', 'main.tsx', 'app.ts', 'app.js', 'server.ts', 'server.js', 'mod.rs', 'main.go', 'main.py', 'main.rs', 'manage.py', 'app.py', 'wsgi.py', 'asgi.py', 'run.py', '__main__.py', 'Application.java', 'Main.java', 'Program.cs', 'config.ru', 'index.php', 'App.swift', 'Application.kt', 'main.cpp', 'main.c']);

function rank(counts, nodeById, key) {
  return [...counts.entries()]
    .filter(([, n]) => n > 0)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 20)
    .map(([id, n]) => ({ id, [key]: n, name: nodeById.get(id)?.name }));
}

function percentile(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))];
}

function main() {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('usage: ua-tour-analyze.js <input.json> <output.json>');
  const { nodes, edges, layers } = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const fanIn = new Map(nodes.map((n) => [n.id, new Set()]));
  const fanOut = new Map(nodes.map((n) => [n.id, new Set()]));
  const forward = new Map(nodes.map((n) => [n.id, []]));
  const pairEdges = new Map();

  for (const e of edges) {
    if (!nodeById.has(e.source) || !nodeById.has(e.target) || e.source === e.target) continue;
    fanIn.get(e.target).add(e.source);
    fanOut.get(e.source).add(e.target);
    if (e.type === 'imports' || e.type === 'calls') forward.get(e.source).push(e.target);
    const key = [e.source, e.target].sort().join('|');
    pairEdges.set(key, (pairEdges.get(key) || 0) + 1);
  }

  const inCounts = new Map([...fanIn].map(([k, v]) => [k, v.size]));
  const outCounts = new Map([...fanOut].map(([k, v]) => [k, v.size]));
  const outTop10 = percentile([...outCounts.values()], 0.9);
  const inBottom25 = percentile([...inCounts.values()], 0.25);

  const scored = nodes.map((n) => {
    const file = n.filePath || '';
    const depth = file.split('/').length - 1;
    let score = 0;
    if (n.type === 'document') {
      if (file === 'README.md') score += 5;
      else if (depth === 0 && file.endsWith('.md')) score += 2;
    } else if (n.type === 'file') {
      if (ENTRY_NAMES.has(path.basename(file))) score += 3;
      if (depth <= 1) score += 1;
      if (outCounts.get(n.id) >= outTop10 && outCounts.get(n.id) > 0) score += 1;
      if (inCounts.get(n.id) <= inBottom25) score += 1;
    }
    return { id: n.id, score, name: n.name, type: n.type, summary: n.summary };
  }).filter((c) => c.score > 0).sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));

  // BFS starts from the top code entry point because documents carry no imports edges.
  const start = scored.find((c) => c.type === 'file' && forward.get(c.id).length > 0) || scored.find((c) => c.type === 'file');
  const order = [];
  const depthMap = {};
  const byDepth = {};
  if (start) {
    depthMap[start.id] = 0;
    const queue = [start.id];
    while (queue.length) {
      const id = queue.shift();
      order.push(id);
      (byDepth[depthMap[id]] ||= []).push(id);
      for (const next of forward.get(id)) {
        if (!(next in depthMap)) {
          depthMap[next] = depthMap[id] + 1;
          queue.push(next);
        }
      }
    }
  }

  const describe = (n) => ({ id: n.id, name: n.name, summary: n.summary });
  const pick = (...types) => nodes.filter((n) => types.includes(n.type)).map(describe);
  const nonCodeFiles = {
    documentation: pick('document'),
    infrastructure: pick('service', 'pipeline', 'resource'),
    data: pick('table', 'schema', 'endpoint'),
    config: pick('config'),
  };

  // Bidirectional pairs seed clusters; imports form a DAG here, so fall back to shared edges when none exist.
  const has = (a, b) => fanOut.get(a).has(b);
  const seeds = [];
  for (const a of nodes) for (const b of nodes) {
    if (a.id < b.id && has(a.id, b.id) && has(b.id, a.id)) seeds.push([a.id, b.id]);
  }
  const clusterEdges = (ids) => ids.reduce((sum, a, i) => sum + ids.slice(i + 1).reduce((s, b) => s + (pairEdges.get([a, b].sort().join('|')) || 0), 0), 0);
  const clusters = seeds.map((seed) => {
    const members = [...seed];
    for (const n of nodes) {
      if (members.length >= 5) break;
      if (members.includes(n.id)) continue;
      const links = members.filter((m) => has(n.id, m) || has(m, n.id)).length;
      if (links >= 2) members.push(n.id);
    }
    return { nodes: members, edgeCount: clusterEdges(members) };
  }).sort((a, b) => b.edgeCount - a.edgeCount);
  const seen = new Set();
  const unique = clusters.filter((c) => {
    const key = [...c.nodes].sort().join('|');
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 10);

  const nodeSummaryIndex = Object.fromEntries(nodes.map((n) => [n.id, { name: n.name, type: n.type, summary: n.summary }]));

  fs.writeFileSync(outputPath, JSON.stringify({
    scriptCompleted: true,
    entryPointCandidates: scored.slice(0, 5),
    fanInRanking: rank(inCounts, nodeById, 'fanIn'),
    fanOutRanking: rank(outCounts, nodeById, 'fanOut'),
    bfsTraversal: { startNode: start?.id ?? null, order, depthMap, byDepth },
    nonCodeFiles,
    clusters: unique,
    layers: { count: layers.length, list: layers },
    nodeSummaryIndex,
    totalNodes: nodes.length,
    totalEdges: edges.length,
  }, null, 2));
}

try {
  main();
} catch (err) {
  console.error(err.message);
  process.exit(1);
}
