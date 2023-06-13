MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR := $(abspath ${MKFILE_PATH}/..)

SHELL:=bash

PROJECT_NAME=shrimpstation
TARGET_DIR:=/home/onze/shrimpstation
TARGET_HOST:=shrimpstation.local

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
	rm -rf /tmp/${PROJECT_NAME}/venv
	python3 -m venv /tmp/${PROJECT_NAME}/venv
	source /tmp/${PROJECT_NAME}/venv/bin/activate
	pip install -r ./ops/requirements.txt

# push code and run it - dev loop
.ONESHELL:
remoterun: pushfiles
	source /tmp/${PROJECT_NAME}/venv/bin/activate
	ssh $(TARGET_HOST) "cd $(TARGET_DIR) && amke localrun"

.ONESHELL:
localrun:
	source /tmp/${PROJECT_NAME}/venv/bin/activate
	python3 main.py
