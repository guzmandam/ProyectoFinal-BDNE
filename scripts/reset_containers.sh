#!/bin/bash

docker compose down -v
docker volume prune -f
docker compose up -d