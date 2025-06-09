#!bin/bash

sudo tcpdump -i any host www.duckdns.org -w duckdns_traffic.pcap &
TCPDUMP_PID=$!

sleep 600
sudo kill $TCPDUMP_PID

tcpdump -r duckdns_traffic.pcap | wc -l
tcpdump -r duckdns_traffic.pcap -q | awk '{print $NF}' | grep -o '[0-9]*' | awk '{sum += $1} END {print sum " bytes total"}'