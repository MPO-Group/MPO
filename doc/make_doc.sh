#!/usr/bin/env bash

MD() {
    if hash pandoc 2>/dev/null; then
	pandoc -f markdown_github -c mpo_doc.css -o $2 $1
    else
	python md_css_generator.py $1 mpo_doc.css $2
    fi
}

for mdfile in *.md; do
    htmlfile="${mdfile%.*}".html
    MD $mdfile $htmlfile
done

SRCLIST='../server/web_server.py ../server/api_server.py\
        ../db/db.py ../client/python/mpo_arg.py'

for SRC in $SRCLIST; do
    python -m  pydoc -w $SRC
done

