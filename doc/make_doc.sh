#!/usr/bin/env bash
for MD in *.md; do
    htmlfile="${MD%.*}".html
    python md_css_generator.py $MD mpo_doc.css $htmlfile
done

SRCLIST='../server/web_server.py ../server/api_server.py\
        ../db/db.py ../client/python/mpo_arg.py'

for SRC in $SRCLIST; do
    python -m  pydoc -w $SRC
done

