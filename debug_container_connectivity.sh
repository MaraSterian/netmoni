#!/bin/bash

echo "=== Docker Container Network Debug ==="
echo "Monitor VM IP: $(hostname -I | awk '{print $1}')"
echo

# Check if containers are running
echo "=== Running Containers ==="
docker-compose ps
echo

# Test internal connectivity from status-page container
echo "=== Testing Internal Connectivity ==="
docker-compose exec status-page bash -c "
echo 'Testing from status-page container:'
echo '- Prometheus:' && curl -s -o /dev/null -w '%{http_code}' http://prometheus:9090/api/v1/label/__name__/values
echo '- OpenSearch:' && curl -s -o /dev/null -w '%{http_code}' http://opensearch:9200/_cluster/health
echo '- Grafana:' && curl -s -o /dev/null -w '%{http_code}' http://grafana:3000/api/health  
echo '- Loki:' && curl -s -o /dev/null -w '%{http_code}' http://loki:3100/ready
echo '- Suricata Exporter:' && curl -s -o /dev/null -w '%{http_code}' http://suricata-exporter:9917/metrics
echo '- Arkime Viewer:' && curl -s -o /dev/null -w '%{http_code}' http://viewer:8005
"

# Check external access (from host/other VMs)
VM_IP=$(hostname -I | awk '{print $1}')
echo
echo "=== External Access URLs ==="
echo "Status Page: http://${VM_IP}:5000"
echo "Grafana: http://${VM_IP}:3000"
echo "Prometheus: http://${VM_IP}:9090" 
echo "Arkime: http://${VM_IP}:8005"
echo "OpenSearch: http://${VM_IP}:9200"

# Check logs
echo
echo "=== Status Page Logs ==="
docker-compose logs --tail=20 status-page