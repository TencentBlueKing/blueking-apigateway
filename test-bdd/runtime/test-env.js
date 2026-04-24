// test-bdd/runtime/test-env.js
// Load test credentials from .test-env.json

const fs = require('fs');
const path = require('path');

const ENV_JSON = path.join(__dirname, '.test-env.json');

if (!fs.existsSync(ENV_JSON)) {
  throw new Error(
    `.test-env.json not found. Create it with:\n` +
    `  {"url": "https://...", "user": "admin", "password": "..."}`
  );
}

const config = JSON.parse(fs.readFileSync(ENV_JSON, 'utf-8'));

module.exports = {
  BASE_URL: config.url || '',
  USERNAME: config.user || '',
  PASSWORD: config.password || '',
  COOKIE:   config.cookie || '',
};
