DEFAULT_GOAL := help

.PHONY: deploy run-native run-docker build-native build-docker publish

dns-name ?= $(shell cat config.yml | yq e '.dns-name')
email ?= $(shell cat config.yml | yq e '.email')
name ?= $(shell cat config.yml | yq e '.name')
port ?= $(shell cat config.yml | yq e '.port')
name-dashed ?= $(subst /,-,$(name))
git-hash ?= $(shell git rev-parse HEAD 2>/dev/null || echo dev)
image-url ?= ghcr.io/$(name)/$(name-dashed):$(git-hash)

help:
	@awk '/^## / \
		{ if (c) {print c}; c=substr($$0, 4); next } \
			c && /(^[[:alpha:]][[:alnum:]_-]+:)/ \
		{printf "%-30s %s\n", $$1, c; c=0} \
			END { print c }' $(MAKEFILE_LIST)

.build: pyproject.toml
	uv lock
	uv export --no-hashes --no-dev --no-emit-project --format requirements-txt -o requirements.txt
	touch .build

## install runtime + dev deps
build-native: .build
	uv sync --group dev

.build-docker:
	docker build \
		--progress plain \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from $(name):latest \
		-t $(name):$(git-hash) \
		-t $(name):latest \
		.

## build project inside a docker container
build-docker: .build .build-docker

.publish:
	docker tag $(name):$(git-hash) $(image-url)
	docker push $(image-url)

## publish the docker image to the registry
publish: build-docker .publish

.deploy:
	env \
		NAME=$(name-dashed) \
		DNS_NAME=$(dns-name) \
		IMAGE=$(image-url) \
		envsubst < deploy/main.yml | kubectl apply -f -

## deploy the application to the cluster
deploy: publish .deploy

## run the FastAPI server locally with autoreload + browser livereload
run-native:
	DEBUG=1 uv run uvicorn eco_spec_tracker.main:app --reload --reload-dir src --port $(port) --host 0.0.0.0

## run the app inside a docker container
run-docker:
	docker run -e PORT=$(port) -p $(port):$(port) -it --rm $(name):latest

## run the C# shell harness on :5100 (same API shape as the real Eco mod)
run-shell:
	cd mod && dotnet run --project shell/EcoJobsTracker.Shell.csproj

## build the real Eco mod DLL (drops in mod/src/bin/Release/net10.0/)
build-mod:
	cd mod && dotnet build src/EcoJobsTracker.csproj -c Release

## verify C# formatting (used by pre-commit)
format-cs:
	cd mod && dotnet format
