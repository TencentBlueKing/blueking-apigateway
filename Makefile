# BlueKing API Gateway - BDD Test Suite
#
# Usage:
#   1. Create test-bdd/runtime/.test-env.json:
#      {"url": "https://example.com", "user": "admin", "password": "secret"}
#      Or with cookie: {"url": "https://example.com", "cookie": "bk_token=abc"}
#
#   2. Run:
#      make test-bdd

.PHONY: test-bdd test-bdd-init test-bdd-install

# Install runtime dependencies, skip if already ready
test-bdd-init:
	@cd test-bdd && \
	if [ -d node_modules ] && \
	   node -e "const p=require('@playwright/test').chromium.executablePath();require('fs').accessSync(p)" 2>/dev/null; then \
		echo "BDD runtime environment is ready, skipping init."; \
	else \
		echo "Setting up BDD runtime environment..."; \
		npm install --silent && \
		npx playwright install chromium --with-deps && \
		echo "BDD runtime environment setup complete."; \
	fi

# Run BDD tests — requires test-bdd/runtime/.test-env.json
test-bdd: test-bdd-init
	@cd test-bdd/runtime && \
		node -e " \
			var fs = require('fs'); \
			var f = '.test-env.json'; \
			if (!fs.existsSync(f)) { \
				console.error('Error: ' + f + ' not found.'); \
				console.error('Create it with: {\"url\": \"...\", \"user\": \"...\", \"password\": \"...\"}'); \
				process.exit(1); \
			} \
			var c = JSON.parse(fs.readFileSync(f, 'utf-8')); \
			if (!c.url) { console.error('Error: \"url\" is required in ' + f); process.exit(1); } \
			if (!c.password && !c.cookie) { console.error('Error: \"password\" or \"cookie\" is required in ' + f); process.exit(1); } \
		" && \
		npx playwright test --config=playwright.config.js
	@echo ""
	@echo "Reports: test-bdd/runtime/reports/"

# Alias for backward compatibility
test-bdd-install: test-bdd-init
