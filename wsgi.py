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
        if 'logged_in' in session:
            print(db.query(Tweet).all())
            tmpl = j2_env.get_template('home.html')
            resp.body = tmpl.render({'tweets': db.query(Tweet).all()})
        else:
            raise falcon.HTTPMovedPermanently('/login')


class Login(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        session = req.env['beaker.session']
        if 'logged_in' in session:
            raise falcon.HTTPMovedPermanently('/')
        else:
            tmpl = j2_env.get_template('login.html')
            resp.body = tmpl.render()

    def on_post(self, req, resp):
        user = db.query(User).filter(User.id == req.params['username']).first()
        if user:
            session = req.env['beaker.session']
            session['logged_in'] = user.id
            session.save()
            raise falcon.HTTPMovedPermanently('/')
        else:
            self.on_get(req, resp)


app = falcon.API()
app.req_options.auto_parse_form_urlencoded = True
app.add_route('/', Home())
app.add_route('/login', Login())
# Configure the SessionMiddleware
session_opts = {
    'session.type': 'file',
    'session.data_dir': 'sessions',
    'session.cookie_expires': True,
}
application = SessionMiddleware(app, session_opts)
