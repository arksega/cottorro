import falcon


class Home(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        with open('www/base.html') as fd:
            resp.body = fd.read()

app = application = falcon.API()
app.add_route('/', Home())
