from jinja2 import Environment, FileSystemLoader
from beaker.middleware import SessionMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from collections import namedtuple
from model import Tweet, User
from base64 import b64encode
import sqlalchemy
import hashlib
import falcon
import os

j2_env = Environment(loader=FileSystemLoader('www/'), trim_blocks=True)

engine = create_engine('sqlite:///cottorro.db')
Session = sessionmaker()
Session.configure(bind=engine)
db = Session()

Alert = namedtuple('Alert', ('level', 'title', 'text'))


class AuthMiddleware(object):

    def process_request(self, req, resp):
        anonym = ('/login', '/', '/signup')
        session = req.env['beaker.session']
        if not session.get('logged_in', None) and req.path not in anonym:
            raise falcon.HTTPFound('/login')


class Home(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        print(db.query(Tweet).all())
        tmpl = j2_env.get_template('home.html')
        xdata = []
        for tw in db.query(Tweet).all():
            shash = hashlib.md5(tw.author.email.lower().encode()).hexdigest()
            tw.img = "https://www.gravatar.com/avatar/" + shash
            xdata.append(tw)
        resp.body = tmpl.render({
            'tweets': xdata,
            'user': session.get('logged_in')
        })


class Login(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        if session.get('logged_in', None):
            raise falcon.HTTPFound('/')
        else:
            tmpl = j2_env.get_template('login.html')
            resp.body = tmpl.render()

    def on_post(self, req, resp):
        user = db.query(User).filter(User.id == req.params['username']).first()
        if user:
            sha256 = hashlib.sha256()
            sha256.update((user.salt + req.params['password']).encode())
            key = sha256.hexdigest()
            if key == user.key:
                session = req.env['beaker.session']
                session['logged_in'] = user.id
                session.save()
                raise falcon.HTTPFound('/')
        ermsg = 'Usuario o contraseña invalidos'
        resp.content_type = 'text/html'
        data = {'alerts': [Alert('urgent', '', ermsg)]}
        tmpl = j2_env.get_template('login.html')
        resp.body = tmpl.render(data)


class Logout(object):

    def on_get(self, req, resp):
        session = req.env['beaker.session']
        session['logged_in'] = None
        session.save()
        raise falcon.HTTPFound('/')


class Signup(object):

    def _error(self, req, resp, msg):
            data = {
                'alerts': [Alert('urgent', '', msg)],
                'username': req.params['username'],
                'email': req.params['email']
            }
            resp.content_type = 'text/html'
            tmpl = j2_env.get_template('signup.html')
            resp.body = tmpl.render(data)

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        tmpl = j2_env.get_template('signup.html')
        resp.body = tmpl.render()

    def on_post(self, req, resp):
        if req.params['password'] != req.params['password2']:
            ermsg = 'Ambos campos de contraseña deben coincidir'
            self._error(req, resp, ermsg)
            return
        salt = b64encode(os.urandom(18)).decode()
        sha256 = hashlib.sha256()
        sha256.update((salt + req.params['password']).encode())
        key = sha256.hexdigest()
        db.add(User(
            id=req.params['username'],
            salt=salt,
            key=key,
            email=req.params['email']))
        try:
            db.commit()
            session = req.env['beaker.session']
            session['logged_in'] = req.params['username']
            session.save()
            raise falcon.HTTPFound('/')
        except sqlalchemy.exc.IntegrityError:
            ermsg = 'El usuarion {} ya existe'.format(req.params['username'])
            self._error(req, resp, ermsg)


class TweetResource(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        tmpl = j2_env.get_template('cottorrear.html')
        resp.body = tmpl.render({'user': session['logged_in']})

    def on_post(self, req, resp):
        session = req.env['beaker.session']
        tx = Tweet(**{
            'author_id': session['logged_in'],
            'text': req.params['text']})
        db.add(tx)
        db.commit()
        raise falcon.HTTPFound('/')

app = falcon.API(middleware=[AuthMiddleware()])
app.req_options.auto_parse_form_urlencoded = True
app.add_route('/', Home())
app.add_route('/login', Login())
app.add_route('/logout', Logout())
app.add_route('/write', TweetResource())
app.add_route('/signup', Signup())
# Configure the SessionMiddleware
session_opts = {
    'session.type': 'file',
    'session.data_dir': 'sessions',
    'session.cookie_expires': True,
}
application = SessionMiddleware(app, session_opts)
