import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path

# JSON Schema describing the structure of a post
song_schema = {
    "properties": {
        "file" : {
            "properties": {
                "id": {"type": "number"}    
            },
            "required": ["id"]
        },
    },
    "required": ["file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    """ Get a list of songs"""
    
    songs = session.query(models.Song).all()
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def song_get(id):
    """ Return single song """
    
    song = session.query(models.Song).get(id)

    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    """ Add a new song"""
    
    data = request.json
    
    # Validate JSON against schema
    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Add song to database
    song = models.Song(file_id=data["file"]["id"])
    session.add(song)
    session.commit()
    
    # Return JSON response and location header
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("song_get", id=song.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")