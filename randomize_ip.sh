#!/bin/bash

while true; do
    NEW_IP="192.168.56.$((RANDOM % 254 + 1))"
    ip addr flush dev ens34
    ip addr add $NEW_IP/24 dev ens34
    echo "New IP assigned: $NEW_IP"
    sleep 60
done