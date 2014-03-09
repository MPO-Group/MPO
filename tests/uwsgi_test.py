def application(env, start_response):
    import os
    start_response('200 OK', [('Content-Type','text/html')])
    print('env '+str(env))
    print('env '+str(env.get('SCRIPT_FILENAME')))
    print('env '+str(env.get('UWSGI_ROUTER')))
    return [b"Hello World"+str(env)+'<br>'+str(os.environ)]
