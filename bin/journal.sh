#!/bin/bash
#
# Script to manage the journal log files
#
# Commands:
#  * status: print current disk usage
#  * size <maxMB>: limit total size to <maxMB> MB of logs
#  * time <maxWks>: limit to <maxWeeks> weeks of logs
#  * number <maxNum>: limit to <maxNum> of log files
#
# N.B. This can be set in /etc/systemd/journald.conf (SystemMaxUse=?M, MaxFileSec=?day)
#

if [ $# -lt 1 ]; then
    echo "Usage: $0 {'status' | 'size <maxMB>' | 'time <maxWks>' | 'number <maxNum>'}"
    exit 1
fi

case $1 in
status)
    echo "Show current journal log file usage"
    sudo journalctl --disk-usage
    ;;
size)
    echo "Limit the journal logs to <maxMB> MB of logs"
    if [ $# -lt 1 ]; then
        echo "Usage: $0 size <maxMB>"
        exit 1
    fi
    MAX_MBS=$2
    sudo journalctl --rotate
    sudo journalctl --vacuum-size=${MAX_MBS}M
    ;;
time)
    echo "Limit the journal logs to <maxWeeks> weeks of logs"
    if [ $# -lt 1 ]; then
        echo "Usage: $0 time <maxWks>"
        exit 1
    fi
    MAX_WEEKS=$2
    sudo journalctl --rotate
    sudo journalctl --vacuum-time=${MAX_WEEKS}weeks
    ;;
number)
    echo "Limit the journal logs to <maxWeeks> weeks of logs"
    if [ $# -lt 1 ]; then
        echo "Usage: $0 number <maxNum>"
        exit 1
    fi
    MAX_NUM=$2
    sudo journalctl --rotate
    sudo journalctl --vacuum-files=${MAX_NUM}
    ;;
*)
    echo "ERROR: invalid argument '$arg' -- must be one of 'status', 'size', 'time', or 'number'" >&2
    exit 1
    ;;
esac    
