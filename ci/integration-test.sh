#!/usr/bin/env bash

docker compose --profile test up --build --abort-on-container-exit --exit-code-from mars_integration_tests mars_integration_tests
