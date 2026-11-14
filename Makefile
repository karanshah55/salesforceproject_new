# Run a chosen sequence of test modules with pytest.
#
#   make test login leads logout   login -> Lead tests (columns + create/edit/delete) -> logout
#   make test contacts accounts    login and logout are added automatically
#   make test                      every test, same as plain `pytest`
#   make test leads ARGS=-v        extra pytest options go in ARGS
#   make list leads                show what would run, without opening the browser
#
# Modules always run in the journey order set in tests/conftest.py (TEST_ORDER),
# whatever order they are typed in.

PYTHON ?= python
ARGS ?=

MODULES := login leads leads_api contacts accounts opportunities products setup logout

ifneq ($(filter $(firstword $(MAKECMDGOALS)),test list),)
  SELECTED := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  UNKNOWN := $(filter-out $(MODULES),$(SELECTED))
  ifneq ($(UNKNOWN),)
    $(error Unknown test module(s): $(UNKNOWN). Choose from: $(MODULES))
  endif
  # The module names are arguments to `test`/`list`, not targets of their own: make them no-ops.
  ifneq ($(SELECTED),)
    $(eval $(SELECTED):;@:)
  endif
endif

.PHONY: help test list

help:
	@echo Usage: make test [modules...] [ARGS=pytest-options]
	@echo Modules: $(MODULES)
	@echo Example: make test login leads logout

TEST_FILES = $(addprefix tests/test_,$(addsuffix .py,$(SELECTED)))

test:
	$(PYTHON) -m pytest $(TEST_FILES) $(ARGS)

# Show which tests a selection would run, without opening the browser.
list:
	$(PYTHON) -m pytest $(TEST_FILES) --collect-only -q
