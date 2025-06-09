while true; do     
    current_ip=$(cat windows_ip.txt);     
    timestamp=$(date '+%H:%M:%S');          
    ping_result=$(ping -c 1 -W 3 $current_ip 2>&1);     
    ping_time=$(echo "$ping_result" | grep "time=" | sed 's/.*time=\([0-9.]*\).*/\1/');          
    if echo "$ping_result" | grep -q "1 received"; then         
        echo "$timestamp: ✓ Connected to $current_ip (${ping_time}ms)";     
    elif echo "$ping_result" | grep -q "Unreachable"; then         
        echo "$timestamp: ✗ Unreachable $current_ip";     
    else         
        echo "$timestamp: ✗ Timeout $current_ip";     
    fi;          
    sleep 1; 
done