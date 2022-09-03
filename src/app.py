import requests
from klein import Klein

app = Klein()

#import routes
from routes import routes

app.run("localhost", 9022)

