# Models are just going to be operations on dictionaries.

from collections import namedtuple as nt
import datetime
import cytoolz as t

def make_date_parser(fmt):
    def date_parser(date_text):
      try:
          return datetime.datetime.strptime(date_text, fmt)
      except ValueError:
          raise ValueError("Incorrect data format, should be "+fmt)
    return date_parser

parse_date = make_date_parser('%Y-%m-%d')
parse_time = make_date_parser('%H:%M:%S')

def date_range(start,end):
    stime = parse_date(start)
    etime = parse_date(end)
    for a in range((etime-stime).days):
        yield (stime + datetime.timedelta(a)).strftime('%Y-%m-%d')


class Student(object):
    def __init__(self, name, id,
                 authorized=None, can_signin=True, can_signout=False,
                 in_class=False, absences=None, deleted=False):
        if authorized is None: authorized = []
        if absences is None: absences = []

        self._name = name
        self._id = id
        self._deleted = deleted
        self._authorized = authorized
        self._can_signin = can_signin
        self._can_signout = can_signout
        self._in_class = in_class
        self._absences = absences

    def __repr__(self):
        return 'Student(name={},id={},can_signin={},can_signout={},in_class={},authorized={},absences={}'.format(
                        self.name, self.id, self.can_signin, self.can_signout, self.in_class, self.authorized, self.absences)

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def deleted(self):
        return self._deleted

    @property
    def can_signin(self):
        return self._can_signin

    @property
    def can_signout(self):
        return self._can_signout

    @property
    def in_class(self):
        return self._in_class

    @property
    def authorized(self):
        return self._authorized

    @property
    def absences(self):
        return self._absences

    @property
    def json(self):
        return t.keymap(lambda k: k[1:] if k.startswith('_') else k, self.__dict__)

    @can_signin.setter
    def can_signin(self,b):
        self._can_signin = b

    @can_signout.setter
    def can_signout(self,b):
        self._can_signout = b

    @in_class.setter
    def in_class(self,b):
        self._in_class = b

    @deleted.setter
    def deleted(self,b):
        self._deleted = b

    def add_authorized(self,user):
        l = len(self.authorized)
        self._authorized.append(user)
        if len(self._authorized) > l:
            return True
        return False

    def remove_authorized(self, user):
        self._authorized.remove(user)

    def add_absence(self,a):
        if isinstance(a,str):
            #will raise valueerror if a is not what is expected.
            parse_date(a)
            self._absences.append(a)

        elif isinstance(a,list):
            if len(a) is not 2:
                raise ValueError('List should have [start,end], length was {}'.format(len(a)))
            parse_date(a[0])
            parse_date(a[1])

            self._absences.extend(date_range(*a))

        else:
            raise ValueError('Should be passing in either string date or an interval.')


class User(object):
    def __init__(self,name,id,permissions=None,deleted=False):
        if permissions == None: permissions = []

        self._name = name
        self._id = id
        self._deleted = deleted
        self._permissions = permissions

    def __repr__(self):
        return 'User(name={},id={},permissions={},deleted={})'.format(
            self.name, self.id, self.permissions, self.deleted)

    @property
    def json(self):
        return t.keymap(lambda k: k[1:] if k.startswith('_') else k,
                        self.__dict__)

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, b):
        self._deleted = b

    @property
    def permissions(self):
        return self._permissions

    def add_permission(self,role):
        self._permissions.append(role)

    def remove_permission(self,role):
        self._permissions.remove(role)


class Interaction(nt('Interaction',
                     ['date', 'student',
                      'time_in', 'time_out'])):
    @property
    def json(self):
        return t.keymap(lambda k: k[1:] if k.startswith('_') else k,
                        dict(self._asdict()))






