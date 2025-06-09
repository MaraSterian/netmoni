# Performance Analysis
## MTD Overhead
### IP randomization CPU
```sh
docker stats win-ip-randomizer --no-stream --format 'CPU: {{.CPUPerc}} | Memory: {{.MemUsage}} | Net I/O: {{.NetIO}}'
```
### SSH connection memory overhead
```sh
docker stats win-ip-randomizer --no-stream --format "{{.Container}} {{.MemUsage}} {{.MemPerc}}
```
### DuckDNS Network Latency added:
```sh
time curl -s "https://www.duckdns.org/update?domains=vvm-mon.duckdns.org&token=a7ce1508-316c-4981-adc5-acd61d51128a&ip=192.168.47.100"
```
###