# pado_visualize dev helper makefile
# ----------------------------------

.PHONY: dev build
.DEFAULT_GOAL := build

build:
	npm run build

dev:
	npm install
