.DEFAULT_GOAL := all
src_path = src
project_path = $(src_path)/kk_plap_generator
mypylint = mypy $(project_path) --ignore-missing-imports --no-warn-unused-ignores --warn-redundant-casts --warn-unused-ignores --pretty --show-error-codes --check-untyped-defs

.PHONY: pretty
pretty:
	ruff format $(project_path)

.PHONY: format
format:
	ruff format $(project_path)
	ruff check --fix
	$(mypylint)

.PHONY: lint
lint:
	ruff check
	$(mypylint)

.PHONY: test
test:
	pytest $(project_path)

.PHONY: run
run:
	python $(src_path)/run_gui.py

.PHONY: bin
bin:
	pyinstaller run_gui.spec 
	mv -f ./dist/run_gui.exe $(src_path)/bin/KoikatsuPlapGenerator.exe

.PHONY: release
release:
	ruff check
	$(mypylint)
	pytest $(project_path)
	pyinstaller run_gui.spec
	mv -f ./dist/run_gui.exe $(src_path)/bin/KoikatsuPlapGenerator.exe
	python $(src_path)/make_release.py

.PHONY: all

all: lint test
