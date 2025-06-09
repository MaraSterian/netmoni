#!/bin/bash

while true; do
  echo "$(date): $(docker stats win-ip-randomizer --no-stream --format 'CPU: {{.CPUPerc}} | Memory: {{.MemUsage}} | Net I/O: {{.NetIO}}')" >> tests/ip_randomizer_cpu_usage.log

done