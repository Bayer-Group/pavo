# pado_visualize dev helper makefile
# ----------------------------------

# sensible make defaults
SHELL := bash
.ONESHELL:
.DELETE_ON_ERROR:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# configuration
# -------------
DOCKER_IMAGE_TAG := pado_visualize

# python deps
python_files := $(shell find pado_visualize -type f -name "*.py") setup.py setup.cfg pyproject.toml MANIFEST.in

# javascript deps
js_files := $(shell find pado_visualize/static_src -type f) package.json package-lock.json .babelrc .eslintrc.json
js_success_file := pado_visualize/static/.done

.DEFAULT_GOAL := docker


environment.docker.yml: environment.devenv.yml
	@echo "generating environment.docker.yml"
	conda devenv -f $< --env PADO_VISUALIZE_DEVEL= --print > $@


${js_success_file}: $(js_files)
	@echo "building js files"
	npm run build
	touch ${js_success_file}


.env_hash: environment.docker.yml setup.cfg setup.py pyproject.toml
	@echo "creating a hash for the python dependencies"
	cat $^ | md5sum | cut -d ' ' -f 1 > $@

.image_id: export PKG_VERSION=$(shell python setup.py --version)
.image_id: export DOCKER_TAG=${DOCKER_IMAGE_TAG}:$(shell python setup.py --version | sed "s/\+/-/")
.image_id: $(python_files) ${js_success_file} Dockerfile .env_hash
	@echo "building docker image"
	@test $${SSH_AUTH_SOCK?Please start ssh-agent and ssh-add your keys for GitHub}
	@echo "using SSH_AUTH_SOCK=$${SSH_AUTH_SOCK}"
	DOCKER_BUILDKIT=1 docker build --ssh default --progress=plain --build-arg ENV_HASH=$(shell cat .env_hash) --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=${PKG_VERSION} --tag="${DOCKER_TAG}" .
	echo "${DOCKER_TAG}" > .image_id


docker: .image_id
	@echo "docker build success"
.PHONY: docker


run: .image_id
	@echo "running docker"
	docker run "$(shell cat .image_id)"
.PHONY: run

debug: .image_id
	@echo "debugging docker"
	docker run -t -i --rm --entrypoint /bin/bash "$(shell cat .image_id)"
.PHONY: debug
