#!/bin/bash

# Check for Suricata configuration
if [ ! -f "/etc/suricata/suricata.yaml" ]; then
  echo "Error: /etc/suricata/suricata.yaml not found!"
  exit 1
fi

# Start Suricata with the desired interface
exec /usr/bin/suricata -c /etc/suricata/suricata.yaml -i ${INTERFACE:-ens34}
