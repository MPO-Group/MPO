#was an attempt at using a decorator
#does not work yet. conflicts with route decorator
#will require separating GET and POST method functions
def broadcast(eventname):
    import functools
    def decorator(routefn):
        @functools.wraps(routefn)
        def wrapper(*args, **kwargs):
            r = routefn(args,kwargs)
            publishEvent(eventname, r)
            return r
        return wrapper
    return decorator
