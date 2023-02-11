#!/usr/bin/bash

export U_ID=$(id -u)
export U_NAME=$(id -un)
export G_ID=$(id -g)
export G_NAME=$(id -gn)

export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-0}

docker-compose $@