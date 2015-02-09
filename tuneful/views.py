from flask import render_template

from tuneful import app

@app.route("/")
def index():
    # Sends static index.html to avoid templating
    return app.send_static_file("index.html")
