#!/usr/bin/env node
// Structural analysis of file-level nodes and edges for architecture layer identification.
const fs = require('fs');

const DIR_PATTERNS = {
  api: ['routes', 'api', 'controllers', 'endpoints', 'handlers', 'serializers', 'controller', 'routers', 'blueprints'],
  service: ['services', 'core', 'lib', 'domain', 'logic', 'signals', 'internal', 'composables', 'mailers', 'jobs', 'channels'],
  data: ['models', 'db', 'data', 'persistence', 'repository', 'repositories', 'entities', 'migrations', 'entity', 'sql', 'database', 'schema'],
  ui: ['components', 'views', 'pages', 'ui', 'layouts', 'screens'],
  middleware: ['middleware', 'plugins', 'interceptors', 'guards'],
  utility: ['utils', 'helpers', 'common', 'shared', 'tools', 'templatetags', 'pkg'],
  config: ['config', 'constants', 'env', 'settings', 'management', 'commands'],
  test: ['__tests__', 'test', 'tests', 'spec', 'specs'],
  types: ['types', 'interfaces', 'schemas', 'contracts', 'dtos', 'dto', 'request', 'response'],
  hooks: ['hooks'],
  state: ['store', 'state', 'reducers', 'actions', 'slices'],
  assets: ['assets', 'static', 'public'],
  entry: ['cmd', 'bin'],
  documentation: ['docs', 'documentation', 'wiki'],
  infrastructure: ['deploy', 'deployment', 'infra', 'infrastructure', 'k8s', 'kubernetes', 'helm', 'charts', 'terraform', 'tf', 'docker'],
  'ci-cd': ['.github', '.gitlab', '.circleci'],
};
const DIR_LOOKUP = new Map(Object.entries(DIR_PATTERNS).flatMap(([label, dirs]) => dirs.map((d) => [d, label])));

function classifyFile(filePath) {
  const base = filePath.split('/').pop();
  if (/\.(test|spec)\.|^test_.*\.py$|_test\.go$|Test\.java$|_spec\.rb$|Test\.php$|Tests\.cs$/.test(base)) return 'test';
  if (base.endsWith('.d.ts')) return 'types';
  if (/^(index\.ts|index\.js|__init__\.py|manage\.py|main\.rs|lib\.rs|Application\.java|Program\.cs|config\.ru)$/.test(base)) return 'entry';
  if (/^(wsgi|asgi)\.py$/.test(base)) return 'config';
  if (/^(Cargo\.toml|go\.mod|Gemfile|pom\.xml|build\.gradle|composer\.json)$/.test(base)) return 'config';
  if (/^Dockerfile|^docker-compose\.|\.tf$|\.tfvars$|^Makefile$/.test(base)) return 'infrastructure';
  if (filePath.startsWith('.github/workflows/') || base === '.gitlab-ci.yml' || base === 'Jenkinsfile') return 'ci-cd';
  if (base.endsWith('.sql')) return 'data';
  if (/\.(graphql|gql|proto)$/.test(base)) return 'types';
  if (/\.(md|rst)$/.test(base)) return 'documentation';
  return null;
}

function commonPrefix(paths) {
  const dirs = paths.map((p) => p.split('/').slice(0, -1));
  if (!dirs.length) return [];
  const prefix = [];
  for (let i = 0; i < dirs[0].length; i += 1) {
    if (dirs.every((d) => d[i] === dirs[0][i])) prefix.push(dirs[0][i]);
    else break;
  }
  return prefix;
}

// Monorepo groups keep two segments for backend/frontend so that api, services and features stay distinct.
function groupOf(filePath, prefixLength) {
  const segments = filePath.split('/').slice(prefixLength);
  if (segments.length === 1) return 'root';
  if (segments[0] === 'backend' && segments[1] === 'app') return segments.length > 3 ? `backend/app/${segments[2]}` : 'backend/app';
  if (segments[0] === 'frontend' && segments[1] === 'src') return segments.length > 3 ? `frontend/src/${segments[2]}` : 'frontend/src';
  if ((segments[0] === 'backend' || segments[0] === 'frontend') && segments.length > 2) return `${segments[0]}/${segments[1]}`;
  return segments[0];
}

function main() {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('usage: ua-arch-analyze.js <input.json> <output.json>');
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const nodes = input.fileNodes || input.nodes;
  const importEdges = input.importEdges || [];
  const allEdges = input.allEdges || [];
  if (!Array.isArray(nodes)) throw new Error('input has no fileNodes or nodes array');

  const pathOf = (n) => n.filePath || n.id.replace(/^[a-z]+:/, '');
  const prefixLength = commonPrefix(nodes.map(pathOf)).length;

  const directoryGroups = {};
  const nodeTypeGroups = {};
  const groupById = new Map();
  const typeById = new Map();
  for (const n of nodes) {
    const group = groupOf(pathOf(n), prefixLength);
    (directoryGroups[group] ||= []).push(n.id);
    (nodeTypeGroups[n.type] ||= []).push(n.id);
    groupById.set(n.id, group);
    typeById.set(n.id, n.type);
  }

  // C. fan-in and fan-out, E. inter-group frequency, F. intra-group density
  const fileFanIn = {};
  const fileFanOut = {};
  const interGroup = new Map();
  const density = Object.fromEntries(Object.keys(directoryGroups).map((g) => [g, { internalEdges: 0, totalEdges: 0, density: 0 }]));
  for (const { source, target } of importEdges) {
    fileFanOut[source] = (fileFanOut[source] || 0) + 1;
    fileFanIn[target] = (fileFanIn[target] || 0) + 1;
    const from = groupById.get(source);
    const to = groupById.get(target);
    if (!from || !to) continue;
    if (from === to) {
      density[from].internalEdges += 1;
      density[from].totalEdges += 1;
    } else {
      density[from].totalEdges += 1;
      density[to].totalEdges += 1;
      const key = `${from}\0${to}`;
      interGroup.set(key, (interGroup.get(key) || 0) + 1);
    }
  }
  for (const d of Object.values(density)) d.density = d.totalEdges ? Number((d.internalEdges / d.totalEdges).toFixed(3)) : 0;
  const interGroupImports = [...interGroup].map(([k, count]) => {
    const [from, to] = k.split('\0');
    return { from, to, count };
  }).sort((a, b) => b.count - a.count);

  const groupRelations = {};
  for (const g of Object.keys(directoryGroups)) groupRelations[g] = { importsFrom: [], importedBy: [] };
  for (const { from, to } of interGroupImports) {
    groupRelations[from].importsFrom.push(to);
    groupRelations[to].importedBy.push(from);
  }

  // D. cross-category edges
  const cross = new Map();
  for (const { source, target, type } of allEdges) {
    const fromType = typeById.get(source);
    const toType = typeById.get(target);
    if (!fromType || !toType) continue;
    const key = [fromType, toType, type].join('\0');
    cross.set(key, (cross.get(key) || 0) + 1);
  }
  const crossCategoryEdges = [...cross].map(([k, count]) => {
    const [fromType, toType, edgeType] = k.split('\0');
    return { fromType, toType, edgeType, count };
  }).sort((a, b) => b.count - a.count);

  // G. pattern matching on the deepest directory segment of each group
  const patternMatches = {};
  for (const g of Object.keys(directoryGroups)) {
    const label = DIR_LOOKUP.get(g.split('/').pop());
    if (label) patternMatches[g] = label;
  }
  const filePatternMatches = {};
  for (const n of nodes) {
    const label = classifyFile(pathOf(n));
    if (label) filePatternMatches[n.id] = label;
  }

  // H. deployment topology
  const paths = nodes.map(pathOf);
  const infraFiles = paths.filter((p) => /(^|\/)(Dockerfile[^/]*|docker-compose[^/]*|Makefile|Jenkinsfile|\.gitlab-ci\.yml)$|\.tfvars?$|^\.github\/workflows\/|(^|\/)(k8s|kubernetes|helm|charts)\//.test(p));
  const deploymentTopology = {
    hasDockerfile: paths.some((p) => /(^|\/)Dockerfile/.test(p)),
    hasCompose: paths.some((p) => /(^|\/)docker-compose/.test(p)),
    hasK8s: paths.some((p) => /(^|\/)(k8s|kubernetes|helm)\//.test(p)),
    hasTerraform: paths.some((p) => /\.tfvars?$/.test(p)),
    hasCI: paths.some((p) => /^\.github\/workflows\/|\.gitlab-ci\.yml$|Jenkinsfile$/.test(p)),
    infraFiles,
  };

  // I. data pipeline
  const dataPipeline = {
    schemaFiles: paths.filter((p) => /\.(sql|graphql|gql|proto|prisma)$/.test(p)),
    migrationFiles: paths.filter((p) => /(^|\/)migrations\//.test(p)),
    dataModelFiles: paths.filter((p) => /(^|\/)(models|repositories|schemas)\//.test(p)),
    apiHandlerFiles: paths.filter((p) => /(^|\/)(routes|api|controllers)\//.test(p)),
  };

  // J. documentation coverage
  const groups = Object.keys(directoryGroups);
  const documented = groups.filter((g) => directoryGroups[g].some((id) => typeById.get(id) === 'document'));
  const docCoverage = {
    groupsWithDocs: documented.length,
    totalGroups: groups.length,
    coverageRatio: groups.length ? Number((documented.length / groups.length).toFixed(2)) : 0,
    undocumentedGroups: groups.filter((g) => !documented.includes(g)),
  };

  // K. dominant dependency direction per group pair
  const dependencyDirection = [];
  const seen = new Set();
  for (const [key, count] of interGroup) {
    const [from, to] = key.split('\0');
    const pair = [from, to].sort().join('\0');
    if (seen.has(pair)) continue;
    seen.add(pair);
    const reverse = interGroup.get(`${to}\0${from}`) || 0;
    if (count === reverse) dependencyDirection.push({ dependent: from, dependsOn: to, mutual: true });
    else if (count > reverse) dependencyDirection.push({ dependent: from, dependsOn: to });
    else dependencyDirection.push({ dependent: to, dependsOn: from });
  }

  const results = {
    scriptCompleted: true,
    directoryGroups,
    nodeTypeGroups,
    crossCategoryEdges,
    interGroupImports,
    groupRelations,
    intraGroupDensity: density,
    patternMatches,
    filePatternMatches,
    deploymentTopology,
    dataPipeline,
    docCoverage,
    dependencyDirection,
    fileStats: {
      totalFileNodes: nodes.length,
      filesPerGroup: Object.fromEntries(groups.map((g) => [g, directoryGroups[g].length])),
      nodeTypeCounts: Object.fromEntries(Object.entries(nodeTypeGroups).map(([t, ids]) => [t, ids.length])),
    },
    fileFanIn,
    fileFanOut,
  };
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
}

try {
  main();
} catch (err) {
  console.error(err.message);
  process.exit(1);
}
