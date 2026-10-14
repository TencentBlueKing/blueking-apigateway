// Static audit indicators are review candidates, not a code/behavior coverage percentage.
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
function filesIn(dir, suffix) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(dir, entry.name);
    return entry.isDirectory() ? filesIn(file, suffix) : file.endsWith(suffix) ? [file] : [];
  });
}

const cases = filesIn(path.join(root, 'cases'), '.md');
const scripts = filesIn(path.join(root, 'scripts'), '.spec.js');
const indicators = [
  ['nonnegative-row-count', /toBeGreaterThanOrEqual\(0\)/g],
  ['conditional-toast', /if\s*\(toast\w*\)/g],
  ['swallowed-download', /waitForEvent\(['"]download['"][^;]*\.catch\(/g],
  ['conditional-visibility', /if\s*\([^\n]*\.isVisible\(/g],
];
const result = {
  caseFiles: cases.length,
  declaredScenarios: 0,
  scriptFiles: scripts.length,
  missingScripts: [],
  scenarioCountDifferences: [],
  scriptsWithoutFailureGuard: [],
  reviewCandidates: [],
};
for (const file of cases) {
  const relative = path.relative(path.join(root, 'cases'), file);
  const source = fs.readFileSync(file, 'utf8');
  const count = [...source.matchAll(/^## 场景[:：]/gm)].length;
  result.declaredScenarios += count;
  const script = path.join(root, 'scripts', relative.replace(/\.md$/, '.spec.js'));
  if (!fs.existsSync(script)) {
    result.missingScripts.push(relative);
    continue;
  }
  const code = fs.readFileSync(script, 'utf8');
  // Parameterized test loops require human comparison of their expanded --list output.
  const testDeclarations = [...code.matchAll(/\btest\(['"`]/g)].length;
  if (count !== testDeclarations) result.scenarioCountDifferences.push({ file: relative, bdd: count, testDeclarations });
}
for (const file of scripts) {
  const relative = path.relative(root, file);
  const code = fs.readFileSync(file, 'utf8');
  if (!/require\(['"][^'"]*runtime\/bdd-test['"]\)/.test(code)) {
    result.scriptsWithoutFailureGuard.push(relative);
  }
  for (const [indicator, pattern] of indicators) {
    const matches = [...code.matchAll(pattern)];
    if (matches.length) result.reviewCandidates.push({
      file: relative, indicator, occurrences: matches.length,
      lines: matches.map(match => code.slice(0, match.index).split('\n').length),
    });
  }
}
console.log(JSON.stringify(result, null, 2));
