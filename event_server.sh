export MPO_EVENT_SERVER_PORT=${1:-9444}
export UDP_EVENTS=yes
export MDS_PATH="/usr/local/cmod/tdi;/usr/local/mdsplus/tdi"
export PATH="/usr/local/mdsplus/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/mdsplus/lib"
#SCRIPT_FILENAME="/usr/local/mdsplus/mdsobjects/python/build/lib/MDSplus/mdsplus_wsgi.py"
#SCRIPT_FILENAME=tests/uwsgi_test.py
#need some local mods for uwsgi support in mdsplus_wsgi.py
SCRIPT_FILENAME="$PWD/server/mdsplus_wsgi.py"
export SCRIPT_FILENAME

#Second argument to WSGIScriptAlias gets set by apache to env SCRIPT_FILENAME
#so we declare it here too since mdsplus_wsgi.py uses this value

uwsgi  \
      --env SCRIPT_FILENAME="/usr/local/mdsplus/mdsobjects/python/build/lib/MDSplus/mdsplus_wsgi.py" \
      --stats 127.0.0.1:9191 \
      --http  "0.0.0.0:$MPO_EVENT_SERVER_PORT" --wsgi-file $SCRIPT_FILENAME  --callable application

