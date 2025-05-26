# mcp-proxy
This project is a proxy for mcp


## develop

- `go 1.23` required

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
