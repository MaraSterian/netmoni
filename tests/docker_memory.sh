#!/bin/bash

while true; do
  echo "$(date): $(docker stats win-ip-randomizer --no-stream --format "{{.Container}} {{.MemUsage}} {{.MemPerc}}" 2>/dev/null || echo "Container not running")" | tee -a docker_memory.log
  sleep 1
done