#!/usr/bin/env bash
# Wait until Wi-Fi/networking has an IPv4 address and a default route.
set -eu

TIMEOUT="${WAIT_FOR_NETWORK_TIMEOUT:-90}"
END=$((SECONDS + TIMEOUT))

while [ "$SECONDS" -lt "$END" ]; do
  if ip -4 route show default 2>/dev/null | grep -q . \
    && hostname -I 2>/dev/null | tr ' ' '\n' | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    exit 0
  fi
  sleep 2
done

echo "Network did not become ready within ${TIMEOUT}s; starting anyway." >&2
exit 0
