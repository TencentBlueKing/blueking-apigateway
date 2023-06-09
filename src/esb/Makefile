# ====== i18n ======

i18n_all: i18n_tpl i18n_mo

i18n_tpl:
	cd esb && pybabel extract -F babel.cfg -c "TRANSLATORS:" . -o babel.po
	cd esb && pybabel update -i babel.po -d locale/locale_api -D django -l en
	cd esb && pybabel update -i babel.po -d locale/locale_api -D django -l zh_Hans

i18n_mo:
	cd esb && django-admin compilemessages -l locale_api/en
	cd esb && django-admin compilemessages -l locale_api/zh_Hans

# ====== dependencies ======

poetry.lock: pyproject.toml
	poetry lock --no-update

.PHONY: requirements
requirements: poetry.lock
	poetry export -f requirements.txt --without-hashes --with dev | grep -v "index-url" > esb/requirements_dev.txt
	poetry export -f requirements.txt --without-hashes | grep -v "index-url" > esb/requirements.txt

VERSION: pyproject.toml
	poetry version | awk '{print $$2}' > esb/VERSION

.PHONY: update
update: VERSION requirements

# ====== test ======

.PHONY: test
test:
	cd esb && . conf/unittest_env && pytest \
		--ds settings \
		--reuse-db \
		--maxfail 1 \
		tests
	rm esb/*.sqlite3 > /dev/null 2>&1 || true

# ====== image ======

.PHONY: _build_dir
_build_dir:
	rm -rf ./build || true
	mkdir build build/bin
	make clean
	cp -r esb/* ./build/
	cp -r bin/* ./build/bin/
	rm -rf ./build/tests
	rm -rf ./build/conf/unittest_env

.PHONY: _clean_build_dir
_clean_build_dir:
	rm -rf ./build || true

.PHONY: _build_image
_build_image:
	$(eval name ?= apigateway-esb)
	$(eval pypi ?= "https://mirrors.cloud.tencent.com/pypi/simple/")
	docker build \
		--no-cache \
		-t "${name}" \
		--build-arg PYPI="${pypi}" \
		.

.PHONY: image
image:
	make _build_dir
	make _build_image
	make _clean_build_dir

.PHONY: dev-image
dev-image:
	make _build_dir
	$(eval pypi ?= "https://mirrors.cloud.tencent.com/pypi/simple/")
	docker build \
		-t "apigateway-esb:development" \
		--build-arg PYPI="${pypi}" \
		.
	make _clean_build_dir

# ====== others ======

.PHONY: lint
lint:
	isort --settings-path=pyproject.toml .
	black --config=pyproject.toml .
	ruff --config=pyproject.toml --force-exclude --fix .
	mypy --config-file=pyproject.toml .

.PHONY: clean
clean:
	find . -name '.mypy_cache' -exec rm -rf {} \; || true
	find . -name '__pycache__' -exec rm -rf {} \; || true
	find . -name '.pytest_cache' -exec rm -rf {} \; || true
	find . -name '*.pyc' -delete || true
	find . -name '*_unittest.sqlite3' -delete || true