const fs = require('fs');
const path = require('path');

const ENV_JSON = path.join(__dirname, '.test-env.json');
const CLI_KEYS = ['URL', 'USER', 'PASSWORD', 'COOKIE'];

function parseMakeFlags(makeFlags) {
  const values = {};

  for (const token of (makeFlags || '').split(/\s+/)) {
    const eqIndex = token.indexOf('=');
    if (eqIndex <= 0) continue;

    const key = token.slice(0, eqIndex);
    if (!CLI_KEYS.includes(key)) continue;

    values[key] = token.slice(eqIndex + 1).replace(/\$\$/g, '$');
  }

  return values;
}

function readExistingConfig() {
  if (!fs.existsSync(ENV_JSON)) {
    return {};
  }

  return JSON.parse(fs.readFileSync(ENV_JSON, 'utf-8'));
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (typeof value === 'string' && value.length > 0) {
      return value;
    }
  }

  return '';
}

const cliOverrides = parseMakeFlags(process.env.MAKEFLAGS || '');
const nextConfig = {
  ...readExistingConfig(),
};

const overrides = {
  url: firstNonEmpty(process.env.TEST_BDD_URL, cliOverrides.URL),
  user: firstNonEmpty(process.env.TEST_BDD_USER, cliOverrides.USER),
  password: firstNonEmpty(process.env.TEST_BDD_PASSWORD, cliOverrides.PASSWORD),
  cookie: firstNonEmpty(process.env.TEST_BDD_COOKIE, cliOverrides.COOKIE),
};

for (const [key, value] of Object.entries(overrides)) {
  if (value) {
    nextConfig[key] = value;
  }
}

if (Object.keys(nextConfig).length === 0) {
  process.exit(0);
}

fs.writeFileSync(ENV_JSON, `${JSON.stringify(nextConfig, null, 2)}\n`);

console.log(
  JSON.stringify({
    url: nextConfig.url || '',
    user: nextConfig.user || '',
    hasPassword: Boolean(nextConfig.password),
    hasCookie: Boolean(nextConfig.cookie),
  })
);