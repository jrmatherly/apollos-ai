#!/bin/bash
set -e

# update apt
apt-get update

# fix permissions for cron files if any
for f in /etc/cron.d/*; do
    [ -f "$f" ] && chmod 0644 "$f"
done

# Prepare SSH daemon
bash /ins/setup_ssh.sh "$@"
