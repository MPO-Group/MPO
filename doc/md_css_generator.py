#!/usr/bin/env python
import markdown
import os, sys
#usage generator.py input.markdown styles.css pretty.html

output = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <style type="text/css">
"""

cssin = open(sys.argv[2])
output += cssin.read()

output += """
    </style>
</head>

<body>
"""
mkin = open(sys.argv[1])
output += markdown.markdown(mkin.read(), ['attr_list'])

output += """</body>

</html>
"""

outfile = open(sys.argv[3],'w')
outfile.write(output)
outfile.close()

