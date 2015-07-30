#!/python3

from bottle import Bottle, route, run, static_file, template
from bottle import request, response, abort, error, HTTPResponse

import json
import toolz as t
import os.path 
import pypandoc
import subprocess
import re

data = json.load(open(os.path.join(os.path.dirname(__file__), 'data.json')))
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
          'body': json.dumps({k:request.params[k] for k in request.params}) 
                  if request.json == None else json.dumps(request.json)}

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
                  str(list(set(keys) - r.keys())))

      if strict and not all(p in keys or p in opts for p in r):
        # since we know that all k in keys is present in r
        # if the lengths are unequal then for sure there are extra keys. 
        jsonabort(400, 'Strict mode: request has unrecognized keys: ' + 
                  str(list(r.keys() - set(keys))))

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

@app.post('/md-render')
@params(['input'], {'out-format': 'html', 'in-format': 'markdown'})
def mdrender(p):
  return {'output' : pypandoc.convert(p['input'], 
                                      p['out-format'], 
                                      format=p['in-format'])}

@app.get('/view/<filename>')
def view_file(filename):
  return subprocess.check_output(['annotator/annotate', 
                                  '-r', '/annotator',
                                  'files/'+filename+'.md'],
                                  universal_newlines=True)

@app.post('/annotate')
@params(['text', 'annotation', 'paragraph', 'premarker', 'postmarker'])
def create_annotation(p):
  """Attempts to annotate `text` in `paragraph` with `annotation`

  Paragraph should contain [premarker, text, postmarker] in that
  order with nothing separating the markers from the text.  
  `annotation` will be applied - so `text` will become 
  `[text](** "annotation")`

  This is COMPLETELY a heuristic and my guess is minimum 2 word len 
  markers in a paragraph will be unique enough to identify some text. 
  Edge case is if the string marks the beginning or end of a paragraph, 
  in which case the special string 'BEGIN' or 'END' is passed appropriately.
  Note, there's no conflict because unless 'BEGIN'/'END', 
  premarker/postmarker should never be 1 word.
  """

  premarker = p['premarker']
  postmarker = p['postmarker']

  if premarker != 'BEGIN' and len(premarker.split()) < 2:
    jsonabort('Invalid premarker len < 2 and not BEGIN') 
  
  if postmarker != 'END' and len(postmarker.split()) < 2:
    jsonabort('Invalid postmarker len < 2 and not END')

  # searching for a string in markdown is actually very difficult - you have
  # to first strip all the formatting so you can match the *rendered* text
  # to the actual string in the file. 
  

# --------------------------- ANNOTATOR STATIC ROUTES

@app.get('/annotator/<resource:path>')
def staticannotator(resource):
  if not resource.endswith('.css') and not resource.endswith('.js'):
    jsonabort('annotator resource request should be css or js file.' 
              'got {}'.format())

  return static_file(resource, root='annotator/')

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


app.run(host='localhost', port=8080, debug=True, reloader=True)





