#!/bin/bash
# Registers AGORA and DAO in the GLP repository's cascade.sh, so that `bash cascade.sh agora` and `bash cascade.sh dao` run the cascade on them.
set -e
G="${1:-.}"
grep -q '^    agora)' "$G/cascade.sh" || sed -i '/^    gai)  FILE=GAI;/a\    agora) FILE=AGORA; OWNER="programs/agora";             PAPER="";                           PLAYDIR="" ;;' "$G/cascade.sh"
grep -q '^    dao)' "$G/cascade.sh" || sed -i '/^    gai)  FILE=GAI;/a\    dao)   FILE=DAO;   OWNER="programs/dao";               PAPER="";                           PLAYDIR="" ;;' "$G/cascade.sh"
