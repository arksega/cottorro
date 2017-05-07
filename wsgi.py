from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import Tweet
import jinja2
import falcon

with open('www/base.html') as fd:
    template = jinja2.Template(fd.read())

engine = create_engine('sqlite:///cottorro.db')
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


class Home(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        print(session.query(Tweet).all())
        resp.body = template.render({'tweets': session.query(Tweet).all()})


app = application = falcon.API()
app.add_route('/', Home())
