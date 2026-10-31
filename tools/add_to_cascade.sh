#!/bin/bash
# Registers AGORA in the GLP repository's cascade.sh, so that `bash cascade.sh agora` runs the cascade on it.
set -e
G="${1:-.}"
grep -q '^    agora)' "$G/cascade.sh" && exit 0
sed -i '/^    gai)  FILE=GAI;/a\    agora) FILE=AGORA; OWNER="programs/agora";             PAPER="";                           PLAYDIR="" ;;' "$G/cascade.sh"
