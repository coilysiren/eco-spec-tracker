DEFAULT_GOAL := help

.PHONY: deploy run-native run-docker build-native build-docker publish test lint format precommit

dns-name ?= $(shell cat coily.yaml | yq e '.dns-name')
email ?= $(shell cat coily.yaml | yq e '.email')
name ?= $(shell cat coily.yaml | yq e '.name')
port ?= $(shell cat coily.yaml | yq e '.port')
name-dashed ?= $(subst /,-,$(name))
git-hash ?= $(shell git rev-parse HEAD 2>/dev/null || echo dev)
# Fully-qualified ref into the in-cluster registry. Forgejo Actions builds
# this, pushes it over plain http (the runner's DinD carries
# --insecure-registry=192.168.0.194:30500), and kai-server's containerd
# pulls it via its registries.yaml insecure entry. See
# coilysiren/infrastructure#168, #171.
image-url ?= 192.168.0.194:30500/$(name-dashed):$(git-hash)

help: ## Print this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-30s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build-native: ## uv lock + uv sync.
	uv lock
	uv sync --group dev

.build-docker:
	docker build \
		--progress plain \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from $(name):latest \
		-t $(name):$(git-hash) \
		-t $(name):latest \
		.

build-docker: .build-docker ## Build the docker image locally with BuildKit cache.

.publish:
	docker tag $(name):$(git-hash) $(image-url)
	docker push $(image-url)

publish: build-docker .publish ## Tag and push the docker image to the in-cluster registry.

.deploy:
	env \
		NAME=$(name-dashed) \
		DNS_NAME=$(dns-name) \
		IMAGE=$(image-url) \
		envsubst < deploy/main.yml | kubectl apply -f -
	kubectl rollout status deployment/$(name-dashed)-app -n $(name-dashed) --timeout=5m

# Stream the rendered manifest over tailscale SSH and apply on kai-server.
# Avoids needing the k3s API reachable from CI — kai-server's own kubectl
# is the path that actually works today (the API only binds to localhost).
.deploy-ssh:
	env \
		NAME=$(name-dashed) \
		DNS_NAME=$(dns-name) \
		IMAGE=$(image-url) \
		envsubst < deploy/main.yml | \
		ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null kai@kai-server \
			'kubectl --kubeconfig=/home/kai/.kube/config apply -f -'

deploy: publish .deploy ## Deploy the application to the cluster.

run-native: ## Run the FastAPI server with autoreload + livereload on port 4100.
	DEBUG=1 uv run uvicorn eco_spec_tracker.main:app --reload --reload-dir src --port $(port) --host 0.0.0.0

run-docker: ## Run the published container locally on port 4100.
	docker run -e PORT=$(port) -p $(port):$(port) -it --rm $(name):latest

run-shell: ## Run the C# shell harness on :5100 (same API shape as the real Eco mod).
	cd mod && dotnet run --project shell/EcoJobsTracker.Shell.csproj

build-mod: ## Build the real Eco mod DLL (drops in mod/src/bin/Release/net10.0/).
	cd mod && dotnet build src/EcoJobsTracker.csproj -c Release

format-cs: ## Verify C# formatting (dotnet format).
	cd mod && dotnet format

test: ## Run the pytest smoke suite.
	uv run pytest

lint: ## ruff check + ruff format --check + mypy on src/ and tests/.
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run mypy src tests

format: ## Apply ruff fixes and formatting in place.
	uv run ruff check --fix src tests
	uv run ruff format src tests

precommit: ## Run all pre-commit hooks against every file.
	uv run pre-commit run --all-files
