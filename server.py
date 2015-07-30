#!/python

from bottle import Bottle, route, run, static_file, template
from bottle import request, response, abort, error, HTTPResponse

import json
import cytoolz as t
import os.path

data = json.load(open(os.path.join(os.path.dirname(__file__), 'data.json')))
def load_data():
    global data
    data = json.load(open(os.path.join(os.path.dirname(__file__), 'data.json')))

def save_data():
    json.dump(data, open(os.path.join(os.path.dirname(__file__), 'data.json'), 'w'), indent=2)

app = Bottle()

# ------------------------------ UTILITIES --------------------------------

def typename(o):
    """Returns classname of `o` in single quotes. eg, typename([]) -> 'list'"""
    return str(type(o))[7:-1]

def reqinfo():
    """Gives path + method + JSON body of request

    This is the minimum information to figure out what went wrong with the
    request that was made to the server.
    """
    return {'path':request.path,
            'method' : request.method,
            'body': {k:request.params[k] for k in request.params}
                    if request.json == None
                    else {k:request.json[k] for k in request.json}}

def jsonabort(status,message):
    """Usage: jsonabort(400, 'message') - works just like abort, but json.

    For JSON REST API, need to be able to send consistent error message with
    a cause statement and a status code, along with some information about the
    request that was made to cause the error.

    this is a parallel function to abort (provided by bottle.py) so use
    accordingly. however, it raises HTTPResponse, and so will NOT be
    caught by other handlers - it's just a clean exit.
    """
    if type(status) is not int:
      abort(500, 'jsonabort requires integer status, got {}'.format(
              typename(status)))
    if type(message) is not str:
      abort(500, 'jsonabort requires string message, got {}'.format(
              typename(message)))

    raise HTTPResponse(status=status, headers={'Content-Type':'application/json'},
                       # TODO(vishesh): should return the entire request object?
                       body=json.dumps({'message':message, 'request':reqinfo()}))

def params(keys=[], opts={}, strict=True):
    """Decorator: Basic request verification for json REST endpoints

    Checks that the request is valid json, that the json returned is an
    object (since lists can lead to XSS attacks and are discouraged in
    json apis) and that all the keys in `keys` are present in the request.

    In strict mode, the request is not allowed to have extraneous keys
    that aren't present in `keys` or `opts`.

    Most requests will want to be strict, I can't imagine why you would
    want a non-key (required field), non-opt (optional field) parameter
    in the request you're making. What other kinds of fields are there?
    However, leaving the option here for the time being - it might be useful
    to relax the requirement while developing and the keys aren't finalized.
    """
    def reqjson(req_fun):
        # pass through all args to req_fun
        def requirejson_wrapper(*args, **kwargs):

            # TODO(vishesh): malformed JSON gives 500 error, should give 400,
            # can't seem to catch the ValueError from json.loads
            try:
                # GET/DELETE have no body. PUT/PATCH/POST have bodies.
                r = None
                if request.method in ['GET', 'DELETE']:
                    r = {k: request.params[k] for k in request.params}
                else:
                    r = request.json
            except ValueError as e:
                jsonabort(400, ('Request should be parseable json, got error: '
                              ''+str(e.args)))

            if r == None:
                # the only time that r will be None is if the json part fails.
                # request.params being empty will give an empty dictionary instead,
                # so this logic is okay (don't need to change the expected
                # content-type based on the request method).
                jsonabort(400, ('Content-Type should be application/json, got '
                                ''+str(request.content_type)))

            if type(r) is not dict:
                jsonabort(400, 'Request must be a JSON object, not {}'.format(
                          typename(r)))

            if not all(k in r for k in keys):
                jsonabort(400, 'Request is missing keys: ' +
                          str(list(set(keys) - set(r.keys()))))

            if strict and not all(p in keys or p in opts for p in r):
                # since we know that all k in keys is present in r
                # if the lengths are unequal then for sure there are extra keys.
                jsonabort(400, 'Strict mode: request has unrecognized keys: ' +
                          str(list(set(r.keys()) - set(keys))))

            # instead of modifying/using global state, choosing to pass in
            # the updated request as a param means that the handler functions
            # are all pure functions of their input params.
            #
            # This should make testing them easier - it's one less thing to mock.
            return req_fun(t.merge(opts, r), *args, **kwargs)

        return requirejson_wrapper
    return reqjson

# converts a dictionary to flat list of key/value pairs.
# each key can have multiple values and they will all be unpacked accordingly.
multipairs=lambda d: list(t.concat(t.map(
                          lambda i: (lambda k,v: t.concat((k,e) for e in v)
                                                if isinstance(v,list)
                                                else (k,v))(i[0],i[1]),
                      d.items())))

# --------------------------------- REST API -------------------------------

@app.get('/')
def index():
    return static_file('index.html', root="static/")

@app.get('/signinout')
@params(keys=['username'])
def signinout(p):
    """Find a user's children."""
    if p['username'] in data['parents']:
        return {'is-child': False, 'children': data['parents'][p['username']]['children']}

    elif p['username'] in data['children']:
        child = data['children'][p['username']]
        if child['in-class']:
            if child['can-signout']:
                # child will just sign themselves out
                child['in-class'] = False
                return {'username': p['username'], 'is-child': True, 'in-class' : False}
            else:
                jsonabort(400, 'Student {} not authorized for self-signout'.format(p['username']))
        else:
            if child['can-signin']:
                # child will sign themselves in
                child['in-class'] = True
                return {'username': p['username'], 'is-child': True, 'in-class': True}
            else:
                jsonabort(400, 'Student {} not authorized for self-signin'.format(p['username']))
    else:
        jsonabort(400, 'User {} does not exist'.format(p['username']))

@app.get('/whosinclass')
def whosinclass():
    return {"present": t.valfilter(lambda c: c['in-class'], data['children'])}

@app.get('/parents')
def get_parents():
    load_data()
    return t.valfilter(lambda v: not v['deleted'], data['parents'])

@app.delete('/parents')
@params(keys=['username'])
def delete_parent(p):
    print "Deleting %s" % (p['username'])
    data['parents'][p['username']]['deleted'] = True
    save_data()

@app.put('/parents')
@params(keys=['username', 'params'])
def update_parent(p):
    print "Updating %s" % (p['username'])
    print "%s = %s" % (p['username'], p['params'])

@app.post('/parents')
@params(keys=['username'])
def create_parent(p):
    print "Creating %s" % (p['username'])

@app.get('/children')
def get_children():
    load_data()
    return t.valfilter(lambda v: not v['deleted'], data['parents'])

@app.delete('/children')
@params(keys=['username'])
def delete_child(c):
    print "Deleting %s" % (p['username'])
    data['children'][p['username']]['deleted'] = True
    save_data()

# --------------------------- BASIC STATIC ROUTES

@app.get('/img/<resource:path>')
def staticimages(resource):
    return static_file(resource, root='static/img/')

@app.get('/fonts/<resource:path>')
def staticfonts(resource):
    return static_file(resource, root='static/fonts/')

@app.get('/lib/<resource:path>')
def staticlib(resource):
    return static_file(resource, root='static/lib/')

@app.get('/js/<resource:path>')
def staticjs(resource):
    return static_file(resource, root='static/js/')

@app.get('/css/<resource:path>')
def staticcss(resource):
    return static_file(resource, root='static/css/')

@app.get('/templates/<resource:path>')
def statictemplates(resource):
    return static_file(resource, root='static/templates/')


#app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
app.run(host='localhost', port=8080, debug=True, reloader=True)




