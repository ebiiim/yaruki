# NOTE: this is temporary until we build `printer` as a web service so that `ui` and `printer` can be deployed separately

VERSION?=$(shell git describe --tags --match "v*")
IMAGE_REGISTRY=localhost
IMAGE_NAME=yaruki

.PHONE: run
run:
	cd ui; venv/bin/streamlit run app.py

.PHONY: image
image:
	docker build -f ./Dockerfile -t $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(VERSION) .

.PHONY: push
push: image
	docker push $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(VERSION)
