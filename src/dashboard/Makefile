FORCE:

.PHONY: init
init:
	pip install -U pip setuptools
	pip install poetry==1.8.4
	poetry install
	pip install pre-commit
	pre-commit install
	mypy --install-types

.PHONY: lint
lint:
	ruff format --config=pyproject.toml --force-exclude .
	ruff check --config=pyproject.toml --force-exclude --fix .
	mypy --config-file=pyproject.toml .
	cd apigateway && lint-imports --config=./.importlinter && cd ..

.PHONY: lint-check
lint-check:
	ruff check --config=pyproject.toml --force-exclude . || (echo "ruff check fail"; exit 1)
	mypy --config-file=pyproject.toml . || (echo "mypy check fail"; exit 1)
	cd apigateway && lint-imports --config=./.importlinter || (echo "importlinter check fail"; exit 1) && cd ..



# ====== dependencies ======

poetry.lock: pyproject.toml
	poetry lock --no-update

.PHONY: requirements
requirements: poetry.lock
	poetry export -f requirements.txt --without-hashes --with dev | grep -v "index-url" > apigateway/requirements_dev.txt
	poetry export -f requirements.txt --without-hashes | grep -v "index-url" > apigateway/requirements.txt

VERSION: pyproject.toml
	poetry version | awk '{print $$2}' > apigateway/VERSION

.PHONY: update
update: VERSION requirements

# ====== test ======

.PHONY: test
test:
	cd apigateway && export PYTHONDONTWRITEBYTECODE=1 && . apigateway/conf/unittest_env && pytest \
		--ds apigateway.settings \
		--reuse-db \
		-n auto \
		--dist loadscope \
		apigateway/tests
	rm apigateway/*.sqlite3 apigateway/dashboard-*.log > /dev/null 2>&1  || true

.PHONY: test-lf
test-lf:
	cd apigateway && . apigateway/conf/unittest_env && pytest \
		--ds apigateway.settings \
		--reuse-db \
		-n auto \
		--dist loadscope \
		--lf \
		apigateway/tests
	rm apigateway/*.sqlite3 apigateway/dashboard-*.log > /dev/null 2>&1  || true

.PHONY: test-cov
test-cov:
	cd apigateway && . apigateway/conf/unittest_env && pytest \
		--ds apigateway.settings \
		--cov=. \
		--reuse-db \
		--maxfail 1 \
		-n auto \
		apigateway/tests
	rm apigateway/*.sqlite3 apigateway/dashboard-*.log > /dev/null 2>&1  || true

.PHONY: test-pdb
test-pdb:
	cd apigateway && . apigateway/conf/unittest_env && pytest \
		-vv \
		--ds apigateway.settings \
		--reuse-db \
		--pdb \
		--maxfail 1 \
		apigateway/tests

.PHONY: tox
tox:
	tox -l
	tox

# ====== edition ======

.PHONY: edition
edition:
	editionctl info

.PHONY: edition-te
edition-te:
	editionctl activate TE

.PHONY: edition-ee
edition-ee:
	editionctl activate EE

.PHONY: edition-develop
edition-develop:
	editionctl develop

.PHONY: edition-reset
edition-reset:
	editionctl reset

# 为 editions 下所有的模块增加 __init__.pyi 以绕过 mypy 的 duplicate module 报错
.PHONY: edition-modules
edition-modules: edition-reset
	find apigateway/apigateway/editions -type d -exec touch {}/__init__.pyi \;

# ====== image ======
#
.PHONY: _build_dir
_build_dir:
	rm -rf ./build || true
	mkdir build build/bin
	make clean
	cp -r apigateway/* ./build/
	cp -r bin/* ./build/bin/
	rm -rf ./build/apigateway/editions
	rm -rf ./build/apigateway/tests
	rm -rf ./build/apigateway/conf/unittest_env
	rm -rf ./build/apigateway/edition-metadata.json
	rm -rf ./build/apigateway/.gitignore

.PHONY: _clean_build_dir
_clean_build_dir:
	rm -rf ./build || true

.PHONY: _build_image
_build_image:
	$(eval name ?= apigateway-dashboard)
	$(eval pypi ?= "https://mirrors.cloud.tencent.com/pypi/simple/")
	docker build \
		--no-cache \
		-t "${name}" \
		--build-arg PYPI="${pypi}" \
		.

.PHONY: image-ee
image-ee:
	editionctl activate --linker-type copy EE
	make _build_dir
	make _build_image
	make _clean_build_dir

.PHONY: image-te
image-te:
	editionctl activate --linker-type copy TE
	make _build_dir
	make _build_image
	make _clean_build_dir

.PHONY: dev-ee-image
dev-ee-image:
	editionctl activate --linker-type copy EE
	make _build_dir
	$(eval pypi ?= "https://mirrors.cloud.tencent.com/pypi/simple/")
	docker build \
		-t "apigateway-dashboard:development" \
		--build-arg PYPI="${pypi}" \
		.
	make _clean_build_dir


# ====== plugins ======

apigateway/fixtures/plugins.yaml: FORCE
	cd apigateway && python manage.py dump_plugin_data -f apigateway/fixtures/plugins.yaml

.PHONY: dump_fixtures
dump_fixtures: apigateway/fixtures/plugins.yaml

.PHONY: load_fixtures
load_fixtures:
	cd apigateway && python manage.py loaddata -i apigateway/fixtures/*.yaml

# ====== others ======

# make messages of python file and django template file to django.po
# python manage.py makemessages -d django -l zh-cn -e html,part -e py
i18n_tpl:
	cd apigateway && python manage.py makemessages -d django -l en -e py

# compile django.po and djangojs.po to django.mo and djangojs.mo
i18n_mo:
	cd apigateway && python manage.py compilemessages

.PHONY: collectstatic
collectstatic:
	cd apigateway && env DJANGO_SETTINGS_MODULE=apigateway.conf.default python manage.py collectstatic

.PHONY: clean
clean:
	find apigateway -name '.mypy_cache' -exec rm -rf {} \; || true
	find apigateway -name '__pycache__' -exec rm -rf {} \; || true
	find apigateway -name '.pytest_cache' -exec rm -rf {} \; || true
	find apigateway -name '*.pyc' -delete || true
	find apigateway -name '*_unittest.sqlite3' -delete || true
	find apigateway -name 'dashboard-*.log' -delete || true
