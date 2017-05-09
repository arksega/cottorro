from jinja2 import Environment, FileSystemLoader
from beaker.middleware import SessionMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import Tweet, User
import falcon

j2_env = Environment(loader=FileSystemLoader('www/'), trim_blocks=True)

engine = create_engine('sqlite:///cottorro.db')
Session = sessionmaker()
Session.configure(bind=engine)
db = Session()


class Home(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        if session.get('logged_in', None):
            print(db.query(Tweet).all())
            tmpl = j2_env.get_template('home.html')
            resp.body = tmpl.render({
                'tweets': db.query(Tweet).all(),
                'user': session.get('logged_in')
            })
        else:
            raise falcon.HTTPFound('/login')


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
            session = req.env['beaker.session']
            session['logged_in'] = user.id
            session.save()
            raise falcon.HTTPFound('/')
        else:
            self.on_get(req, resp)


class Logout(object):

    def on_get(self, req, resp):
        session = req.env['beaker.session']
        session['logged_in'] = None
        session.save()
        raise falcon.HTTPFound('/')


class TweetResource(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        if not session.get('logged_in', None):
            raise falcon.HTTPFound('/login')
        tmpl = j2_env.get_template('cottorrear.html')
        resp.body = tmpl.render({'user': session['logged_in']})

    def on_post(self, req, resp):
        session = req.env['beaker.session']
        if not session.get('logged_in', None):
            raise falcon.HTTPFound('/login')
        tx = Tweet(**{
            'author_id': session['logged_in'],
            'text': req.params['text']})
        db.add(tx)
        db.commit()
        raise falcon.HTTPFound('/')

app = falcon.API()
app.req_options.auto_parse_form_urlencoded = True
app.add_route('/', Home())
app.add_route('/login', Login())
app.add_route('/logout', Logout())
app.add_route('/write', TweetResource())
# Configure the SessionMiddleware
session_opts = {
    'session.type': 'file',
    'session.data_dir': 'sessions',
    'session.cookie_expires': True,
}
application = SessionMiddleware(app, session_opts)
