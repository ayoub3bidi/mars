#!/usr/bin/env bash

docker compose --profile test up --build --abort-on-container-exit mars_linter
