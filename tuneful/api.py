import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from sqlalchemy.orm import exc
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

def get_object(model, id):
    """ Return one record or 404 error if doesn't exist """

    data = session.query(model).get(id)
    
    if data:
        return data
    else:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
    
def validate_schema(data, schema):
    """ Validate JSON against schema and return response if error """        

    try:
        validate(data, schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

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
    
    song = get_object(models.Song, id)
    
    if type(song) == Response:
        return song

    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    """ Add a new song"""
    
    data = request.json
    
    # Validate JSON against schema
    validate_response = validate_schema(data, song_schema)
    if type(validate_response) == Response:
        return validate_response
    
    # Add song to database
    song = models.Song(file_id=data["file"]["id"])
    session.add(song)
    session.commit()
    
    # Return JSON response and location header
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("song_get", id=song.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_put(id):
    """ Update an existing song"""
    
    data = request.json
    
    song = get_object(models.Song, id)
    
    # Test whether song exists
    if type(song) == Response:
        return song
    
    # Validate JSON against schema
    validate_response = validate_schema(data, song_schema)
    if type(validate_response) == Response:
        return validate_response
    
    song.file_id = data["file"]["id"]
    session.commit()
    headers = {"Location": url_for("song_get", id=song.id)}
    
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, headers=headers,
                mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def songs_delete(id):
    """ Delete an existing song"""
    
    song = get_object(models.Song, id)
    
    # Test whether song exists
    if type(song) == Response:
        return song    
    
    session.delete(song)
    session.commit()
    
    message = "Song {} deleted".format(id)
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    """ Return uploaded file """
    return send_from_directory(upload_path(), filename)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    """ Upload file to folder """
    
    # Access file
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Return file name
    filename = secure_filename(file.filename)  # 'secure_filename' prevents injection of malicious files
    # Add file to database
    db_file = models.File(name=filename)
    session.add(db_file)
    session.commit()
    # Save file to upload folder using 'upload_path' function from utils.py
    file.save(upload_path(filename))

    # Return dictionary with file data in JSON
    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")