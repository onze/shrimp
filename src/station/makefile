MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR := $(abspath ${MKFILE_PATH}/..)

SHELL:=bash

PROJECT_NAME:=shrimpstation
TARGET_DIR:=/home/onze/shrimpstation
TARGET_HOST:=shrimpstation.local
VENV_DIR:=/home/onze/tmp/$(PROJECT_NAME)/venv

PYTHON:=python3.9

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
	ssh -t $(TARGET_HOST) "cd $(TARGET_DIR) && make localdeploy"

# initial setup. pretty long on the zero...
.ONESHELL:
localdeploy:
	cd $(ROOT_DIR)
	rm -rf $(VENV_DIR)
	$(PYTHON) -m venv $(VENV_DIR)
	source $(VENV_DIR)/bin/activate
	pip install -r ./ops/requirements.txt
	# install websocat
	mkdir -p ~/.local/bin
	cd ~/.local/bin
	rm -rf ./websocat
	wget https://github.com/vi/websocat/releases/download/v1.12.0/websocat.x86_64-unknown-linux-musl -O websocat
	#wget https://github.com/vi/websocat/releases/download/v1.11.0/websocat.arm-unknown-linux-musleabi -O websocat
	chmod +x ./websocat

# push code and run it - dev loop
.ONESHELL:
remoterun: pushfiles
	ssh -t $(TARGET_HOST) "cd $(TARGET_DIR) && make localrun"

.ONESHELL:
localrun:
	#sudo fuser -k 5000/tcp 5001/tcp
	source $(VENV_DIR)/bin/activate
	python main.py
