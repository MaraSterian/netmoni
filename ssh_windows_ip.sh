#!/bin/bash

WINDOWS_USER="administrator"
WINDOWS_IP_FILE="/tmp/windows_ip.txt"
WINDOWS_HOSTNAME="vvm"
DUCKDNS_TOKEN="a7ce1508-316c-4981-adc5-acd61d51128a"
DUCKDNS_DOMAIN="vvm-mon.duckdns.org"
SOCKET_PATH="/tmp/ssh_sockets/vvm"

cleanup() {
    echo "Cleaning up..."
    if [[ -n "$SSH_PID" ]]; then
        kill $SSH_PID 2>/dev/null
    fi
    # Close existing master connection if it exists
    ssh -S "$SOCKET_PATH" -O exit $WINDOWS_USER@192.168.56.101 2>/dev/null
    rm -f "$SOCKET_PATH"
}
trap cleanup EXIT

cleanup

if [[ -f "$WINDOWS_IP_FILE" ]]; then
   WINDOWS_IP=$(cat "$WINDOWS_IP_FILE")
else
   WINDOWS_IP="192.168.47.138"
fi

curl "https://www.duckdns.org/update?domains=$DUCKDNS_DOMAIN&token=$DUCKDNS_TOKEN&ip=$WINDOWS_IP"

echo "Current vvm IP: $WINDOWS_IP"

mkdir -p /tmp/ssh_sockets

echo "persistent SSH connection"
ssh -o StrictHostKeyChecking=no -i ~/.ssh/windows_key -M -S $SOCKET_PATH $WINDOWS_USER@192.168.56.101 -N &
SSH_PID=$!

sleep 5
if ! ssh -S $SOCKET_PATH $WINDOWS_USER@192.168.56.101 "echo 'Connection test'" 2>/dev/null; then
    echo "Failed to establish SSH connection!"
    exit 1
fi

EXCLUDED_IPS=("192.168.47.1" "192.168.47.2" "192.168.47.131" "192.168.47.128")

while true; do

    while true; do
        NEW_IP="192.168.47.$((RANDOM % 254 + 1))"

        if [[ ! " ${EXCLUDED_IPS[@]}" =~ " ${NEW_IP} " ]]; then
            break
        fi
    done
    
    SSH_COMMAND="Remove-NetIPAddress -InterfaceAlias Ethernet0 -Confirm:\$false; New-NetIPAddress -InterfaceAlias Ethernet0 -IPAddress $NEW_IP -PrefixLength 24; exit"
    ssh -S $SOCKET_PATH $WINDOWS_USER@192.168.56.101 "powershell -Command \"$SSH_COMMAND\""

    echo "Verifying new IP $NEW_IP is active..."
    for i in {1..15}; do
        if ping -c 1 -W 2 $NEW_IP > /dev/null 2>&1; then
            echo "Windows VM responding at: $NEW_IP"
            break
        fi
        sleep 10
    done

    curl "https://www.duckdns.org/update?domains=$DUCKDNS_DOMAIN&token=$DUCKDNS_TOKEN&ip=$NEW_IP"
    WINDOWS_IP="$NEW_IP"

    echo "Windows VM IP updated to: $NEW_IP"
    echo "$NEW_IP" | tee "$WINDOWS_IP_FILE"

    echo "DuckDNS updated with new IP: $NEW_IP"

    sleep 120
    
done
