#!/bin/bash
# Registers the experimental contracts in the GLP repository's cascade.sh, so that `bash cascade.sh <name>` runs the cascade on each.
set -e
G="${1:-.}"
for c in agora dao fdao stay lib ldao joint rec; do
  C=$(echo $c | tr a-z A-Z)
  grep -q "^    $c)" "$G/cascade.sh" || sed -i "/^    gai)  FILE=GAI;/a\\    $c) FILE=$C; OWNER=\"programs/$c\"; PAPER=\"\"; PLAYDIR=\"\" ;;" "$G/cascade.sh"
done
