MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR := $(abspath ${MKFILE_PATH}/..)

SHELL:=bash

TARGET_DIR:=/home/onze/shrimp
TARGET_HOST:=shrimp.local

# only update sources
.ONESHELL:
pushfiles:
	rsync -P -rvc --include tags \
		--cvs-exclude \
		--delete \
		$(ROOT_DIR)/* $(TARGET_HOST):$(TARGET_DIR)/

# also reinstall libs
.ONESHELL:
remotedeploy: pushfiles
	ssh $(TARGET_HOST) "cd $(TARGET_DIR) && make localdeploy"

# initial setup. pretty long on the zero...
.ONESHELL:
localdeploy:
	cd $(ROOT_DIR)
	rm -rf /tmp/venv
	python3 -m venv /tmp/venv
	source /tmp/venv/bin/activate
	pip install -r ./ops/requirements.txt

# push code and run it - dev loop
.ONESHELL:
remoterun: pushfiles
	source /tmp/venv/bin/activate
	python3 main.py
