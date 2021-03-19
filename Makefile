# pado_visualize dev helper makefile
# ----------------------------------

.PHONY: dev watch build
.DEFAULT_GOAL := build

build:
	npm run build

dev:
	npm install

watch:
	npm run watch
