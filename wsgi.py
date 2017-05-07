import falcon


class Home(object):

    def on_get(self, req, resp):
        resp.body = 'Hola mundo Web!'

app = application = falcon.API()
app.add_route('/', Home())
