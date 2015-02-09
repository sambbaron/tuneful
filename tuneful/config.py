class DevelopmentConfig(object):
    DATABASE_URI = "postgresql://action:action@localhost:5432/tuneful"
    DEBUG = True
    UPLOAD_FOLDER = "uploads"

class TestingConfig(object):
    DATABASE_URI = "postgresql://action:action@localhost:5432/tuneful_test"
    DEBUG = True
    UPLOAD_FOLDER = "test-uploads"
