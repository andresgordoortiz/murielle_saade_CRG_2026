#!/usr/bin/env bash
set -euo pipefail

# Supply TOWER_ACCESS_TOKEN in the environment, or paste it at the hidden prompt.
if [[ -z ${TOWER_ACCESS_TOKEN:-} ]]; then
    read -r -s -p 'Seqera access token: ' TOWER_ACCESS_TOKEN
    printf '\n'
fi
if [[ -z $TOWER_ACCESS_TOKEN ]]; then
    echo 'A Seqera access token is required.' >&2
    exit 1
fi
export TOWER_ACCESS_TOKEN
exec bash "$(dirname "${BASH_SOURCE[0]}")/scripts/submit.sh"
