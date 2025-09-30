#!/bin/bash
#
# Script to manage the installed headless RasPi services -- comitup and infoDisplay
#
# Commands:
#  * status: print status of the services
#  * start: enable and start both services
#  * stop: disable and stop both services

if [ $# -ne 1 ]; then
    echo "Usage: $0 {'status' | 'start' | 'stop'}"
    exit 1
fi

# Convert all arguments to lowercase
args=()
for arg in "$@"; do
  args+=( "$(echo "$arg" | tr 'A-Z' 'a-z')" )
done

for arg in "${args[@]}"; do
    case "$arg" in
    status)
        echo "Show status of infoDisplay and comitup services"
        ACTION="status"
        ;;
    start)
        echo "Enable and start infoDisplay and comitup services"
        ACTION="enable"
        ;;
    stop)
        echo "Stop and disable infoDisplay and comitup services"
        ACTION="disable"
        ;;
    *)
        echo "ERROR: invalid argument '$arg' -- must be one of 'status', 'start', or 'stop'" >&2
        exit 1
        ;;
    esac    

done

sudo systemctl --now --no-pager ${ACTION} infoDisplay
echo ""
sudo systemctl --now --no-pager ${ACTION} comitup
echo ""
