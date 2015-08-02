#!/usr/bin/env python

from bottle import Bottle, route, run, static_file, template, TEMPLATE_PATH
from bottle import request, response, abort, error, HTTPResponse

import json
import cytoolz as t
import cytoolz.curried as tc
import os.path
import models as m
import datetime

data = {}
def load_data():
  global data
  data = json.load(open(os.path.join(os.path.dirname(__file__), 'data.json')))
  data['students'] = {s['name']:m.Student(**s) for s in data['students']}
  data['users'] = {u['name']:m.User(**u) for u in data['users']}
  data['interactions'] = map(lambda i: m.Interaction(**i), data['interactions'])


def json_data(data):
  return {'users': map(lambda i: i.json, data['users'].values()),
          'students': map(lambda i: i.json, data['students'].values()),
          'interactions': map(lambda i: i.json, data['interactions'])}
def save_data():
  json.dump(json_data(data),
            open(os.path.join(os.path.dirname(__file__), 'data.json'), 'w'),
            indent=2)

load_data()
app = Bottle()
TEMPLATE_PATH.append('./static/')

# ------------------------------------------------------------------------
#                               UTILITIES
# ------------------------------------------------------------------------

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
                if (request.method in ['GET', 'DELETE'] or
                   (request.method == 'POST' and
                    'json' not in request.content_type)):
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

# --------------------------------------------------------------------------
#                                      REST API
# --------------------------------------------------------------------------
@app.get('/')
def default(message=''):
  return template('signin', message=message)

@app.post('/signin')
@params(keys=['barcode'])
def signin(p):
  u = filter(lambda v: v.id == p['barcode'], data['users'].values())
  if len(u) > 0:
    return template('parent-signin.tpl',
                    students=map(_g('name'), filter(lambda v: u[0].name in v.authorized,
                                    data['students'].values())),
                    name=u[0].name)

  c = filter(lambda s: s.id == p['barcode'], data['students'].values());
  if len(c) > 0:
    print 'is student'
    # should only ever actually equal 1.
    if not c[0].in_class:
      if c[0].can_signin:
        c[0].in_class(True)
        return static_file('success.html', root='static/templates')
      else:
        return template('signin',message='Student ' + c[0].name +
                       ' not authorized for self-signin.')

@app.get('/admin')
def index():
  return static_file('index.html', root="static/")

# @app.get('/signinout')
# @params(keys=['username'])
# def signinout(p):
#     """Find a user's children."""
#     if p['username'] in data['parents']:
#         return {'is-child': False, 'children': data['parents'][p['username']]['children']}

#     elif p['username'] in data['children']:
#         child = data['children'][p['username']]
#         if child['in-class']:
#             if child['can-signout']:
#                 # child will just sign themselves out
#                 child['in-class'] = False
#                 return {'username': p['username'], 'is-child': True, 'in-class' : False}
#             else:
#                 jsonabort(400, 'Student {} not authorized for self-signout'.format(p['username']))
#         else:
#             if child['can-signin']:
#                 # child will sign themselves in
#                 child['in-class'] = True
#                 return {'username': p['username'], 'is-child': True, 'in-class': True}
#             else:
#                 jsonabort(400, 'Student {} not authorized for self-signin'.format(p['username']))
#     else:
#         jsonabort(400, 'User {} does not exist'.format(p['username']))

@app.get('/whosinclass')
def whosinclass():
    return t.reduceby(lambda s: 'present' if s[1] else 'absent' if s[2] else 'nothere',
                      lambda acc,x: acc + [x[0]],
                      [[s.name,
                        s.in_class,
                        datetime.datetime.today().strftime("%Y-%m-%d") in s.absences]
                       for s in data['students'].values()],
                      [])


@app.get('/fulldatadump')
@params(opts={'password':None})
def fulldatadump(p):
    """Required because Heroku has no real file system, so if something
       needs to change, then you have to download all the data first."""
    if p['password'] == 'secret password':
        return json_data(data)
    else:
        abort(404, "Not found: '/fulldatadump'")

# ---------- Interaction Routes --------------------

_g = lambda p: lambda x: getattr(x,p)

@app.get('/interactions')
def get_interactions():
    dates = sorted(set(map(_g('date'), data['interactions'])))
    d = t.pipe(data['interactions'],
               tc.groupby(lambda i: i.student),
               tc.valmap(lambda x: t.pipe(t.groupby(lambda i: i.date,x),
                                          tc.valmap(lambda v: [v[0].time_in, v[0].time_out]))))

    mat = [['student'] + dates]
    for student, attendance in d.items():
        record = [student]
        for dt in dates:
            if dt in attendance:
                record.append(attendance[dt])
            elif dt in data['students'][student].absences:
                record.append(('',''))
            else:
                record.append((None,None))
        mat.append(record)

    return {'interactions': mat}


@app.post('/interactions')
@params(keys=['date', 'student', 'time_in', 'time_out'])
def create_interaction(p):
    try:
      m.parse_date(p['date'])
    except:
      jsonabort(400, "{} is not a date string in the form YYYY-mm-dd".format(
          p['date']))

    if p['student'] not in data['students']:
      jsonabort(400, 'Student {} does not exist'.format(p['student']))

    try:
      m.parse_date(p['time_in'])
    except:
      jsonabort(400, "{} is not a time string in the form HH:mm:ss".format(
          p['date']))

    try:
      m.parse_date(p['time_out'])
    except:
      jsonabort(400, "{} is not a date string in the form HH:mm:ss".format(
          p['date']))

    data['interactions'].append(m.Interaction(**p))



# ------------------ USER ROUTES ----------------

@app.get('/users')
def get_users():
    return {k:v.json for k,v in
            t.valfilter(lambda v: not v.deleted, data['users']).iteritems()}

@app.put('/users')
@params(keys=['username', 'params'])
def update_user(p):
    data['users'][p['username']] = m.User(**p['params'])
    save_data()

@app.put('/users/create')
@params(keys=['username', 'id'])
def create_user(p):
    print "Creating user {}".format(p['username'])
    data['users'][p['username']] = m.User(id=p['id'], name=p['username'])
@app.put('/users/remove-permission')
@params(keys=['username', 'permission'])
def user_remove_perm(p):
    print "Removing {} from {}'s permissions".format(p['permission'], p['username'])
    data['users'][p['username']].remove_permission(p['permission'])
    save_data()


@app.get('/students')
def get_students():
    load_data()
    return {k:v.json for k,v in
            t.valfilter(lambda v: not v.deleted, data['students']).iteritems()}

@app.put('/students')
@params(keys=['username', 'params'])
def update_student(p):
    print "Updating {}".format(p['username'])
    print "{} = {}".format(p['username'], p['params'])
    data['students'][p['username']] = m.Student(**p['params'])
    save_data()

@app.put('/students/create')
@params(keys=['username', 'params'])
def create_student(p):
    print "Creating student {}".format(p['username'])
    data['students'][p['username']] = m.Student(name=p['username'], **p['params'])
    save_data()

@app.put('/students/patch')
@params(keys=['username', 'param'])
def patch_student(p):
    print "Patching {}".format(p['username'])
    key = p['param'][0]
    val = p['param'][1]
    data['students'][p['username']].__setattr__(key, val)

@app.put('/users/add-permission')
@params(keys=['username', 'permission'])
def user_add_perm(p):
    print "Adding {} to {}'s permissions".format(p['permission'], p['username'])
    data['users'][p['username']].add_permission(p['permission'])
    save_data()


@app.put('/students/add-authorized')
@params(keys=['username', 'signer'])
def student_add_authorized(p):
    print "Adding {} to {}'s authorized signers".format(p['signer'], p['username'])
    data['students'][p['username']].add_authorized(p['signer'])
    save_data()

@app.put('/students/remove-authorized')
@params(keys=['username', 'signer'])
def student_remove_authorized(p):
    print "Removing {} from {}'s authorized signers".format(p['signer'], p['username'])
    data['students'][p['username']].remove_authorized(p['signer'])
    save_data()


# --------------------------- BASIC STATIC ROUTES
@app.post('/add-absence')
@params(keys=['student', 'startdate', 'enddate'])
def add_absence(p):
    if p['student'] not in data['students']:
      jsonabort(400, 'Could not find student in database')

    try:
        m.parse_date(p['startdate'])
        m.parse_date(p['enddate'])
    except:
        jsonabort(400, '{} or {} is not in the form YYYY-mm-dd'.format(
          p['startdate'], p['enddate']))

    if p['enddate'] < p['startdate']:
        jsonabort(400, 'Enddate should be greater than startdate')

    if p['enddate'] == p['startdate']:
        data['students'][p['student']].add_absence(p['startdate'])

    data['students'][p['student']].add_absence(p['startdate'], p['enddate'])
    return data['students'][p['student']].json


# ------------------------------------------------------------------------
#                            BASIC STATIC ROUTES
# ------------------------------------------------------------------------

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

if __name__ == '__main__':
  #app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  app.run(host='localhost', port=8080, debug=True, reloader=True)




