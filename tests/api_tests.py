import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())
        
    def testGetSongs(self):
        """ Get all songs from database and return JSON """
        
        # Add new songs
        fileA = models.File(name="Test File 1")
        songA = models.Song(file_id=1)
        fileB = models.File(name="Test File 2")
        songB = models.Song(file_id=2)
        session.add_all([fileA, songA, fileB, songB])
        session.commit()
        
        # Return response
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
        
        # Test status code, mimetype, and number of rows
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        songA = data[0]
        self.assertEqual(songA["file"]["name"], "Test File 1")
        songB = data[1]
        self.assertEqual(songB["file"]["name"], "Test File 2")

    def testGetSong(self):
        """ Get single song from database and return JSON """
        
        # Add new songs
        fileA = models.File(name="Test File 1")
        songA = models.Song(file_id=1)
        fileB = models.File(name="Test File 2")
        songB = models.Song(file_id=2)
        session.add_all([fileA, songA, fileB, songB])
        session.commit()
        
        # Return response
        response = self.client.get("/api/songs/2",
            headers=[("Accept", "application/json")]
        )
        
        # Test status code, mimetype, and number of rows
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        song = json.loads(response.data)
        self.assertEqual(song["file"]["name"], "Test File 2")
        
    def testGetSongNoExists(self):
        """ Get single song from database that does not exist """
        
        # Return response
        response = self.client.get("/api/songs/2",
            headers=[("Accept", "application/json")]
        )
        
        # Test status code, mimetype, and number of rows
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find song with id 2")
                
    def testPostSong(self):
        """ Add single song  """
        
        # Add file prior to testing song
        file = models.File(name="Test Song")
        session.add(file)
        session.commit()
        
        # Song post data
        song = {"file": {"id": 1}}
        
        response = self.client.post("/api/songs",
            data = json.dumps(song),
            content_type = "application/json",
            headers = [("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs/1")
        
        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["file"]["name"], "Test Song")
        
        songs = session.query(models.Song).all()
        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file.name, "Test Song")

    def testPostSongInvalidFile(self):
        """ Add single song without proper file id """
        
        # Add file prior to testing song
        file = models.File(name="Test Song")
        session.add(file)
        session.commit()
        
        # Song post data
        song = {"file": {"id": "0"}}
        
        response = self.client.post("/api/songs",
            data = json.dumps(song),
            content_type = "application/json",
            headers = [("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)
        
    def testPostSongNoFile(self):
        """ Add single song without file """
        
        # Add file prior to testing song
        file = models.File(name="Test Song")
        session.add(file)
        session.commit()
        
        # Song post data
        song = {"wrong": "data"}
        
        response = self.client.post("/api/songs",
            data = json.dumps(song),
            content_type = "application/json",
            headers = [("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)    
        
    def testPutSong(self):
        """ Update song """
        
        # Add new song
        file1 = models.File(name="Test Song")
        file2 = models.File(name="Another Test Song")
        song = models.Song(file_id=1)
        session.add_all([file1, file2, song])
        session.commit()
        
        # Data to change song from File 1 to File 2
        data = {"file": {"id": 2}}
        
        # Send PUT request and return response
        response = self.client.put("/api/songs/1", 
            data = json.dumps(data),
            content_type = "application/json",                                   
            headers = [("Accept", "application/json")]                                  
        )
        
        # Test PUT response status code, mimetype, and location header
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs/1")
        
        # Test post content from response
        data = json.loads(response.data)
        self.assertEqual(data["file"]["name"], "Another Test Song")
        
        # Query post from database
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        # Test post content from database
        song = songs[0]
        self.assertEqual(song.file.name, "Another Test Song")
        
    def testDeleteSong(self):
        """ Delete a song """
        
        file = models.File(name="Test Song")
        song = models.Song(file_id=1)
        session.add_all([file, song])
        session.commit()
        
        response = self.client.delete("/api/songs/1",
            content_type = "application/json",
            headers = [("Accept", "application/json")]
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(data["message"], "Song 1 deleted")
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 0)
        
    def test_get_uploaded_file(self):
        """ Retreive uploaded file through HTTP request """
        
        # Use 'upload_path' function from utils.py to get file location
        # Create file
        path = upload_path("test.txt")
        # Write to file
        with open(path, "w") as f:
            f.write("File contents")
        
        # Use GET request to retreive file
        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, "File contents")
        
        
if __name__ == "__main__":
    unittest.main()        