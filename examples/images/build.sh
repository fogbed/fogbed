#!/bin/bash

docker image build -t sensor ./sensor
docker image build -t fog ./fog
docker image build -t manager ./manager
docker image build -t cloud ./cloud