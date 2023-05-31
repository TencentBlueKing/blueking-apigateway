# core-api

This project provides some APIs for `APISIX/Plugins` and `OpenAPI`.

note:

- depends on database only
- use cache, should be fast


## layers

> view(api/*/*.go) -> service -> cache -> dao -> database

- `view` only do the validation and conversion
- `service` do the business logic
- `cache` only care about the cache
- `dao` do the query
- `database` is the database of bk-apigateway

## develop

- `go 1.20` required

build and run

```bash
# install tools
make init

# download vendor
make dep

# build
make build

# build and serve
make serve

```

develop and test

```bash
# test
make test

# generate mock files
make mock


# do format
make fmt

# check lint
make lint

# build image
make dev-image
```
