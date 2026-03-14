from flask import Flask, redirect
from flask_restful import Api
from flasgger import Swagger
from werkzeug.exceptions import HTTPException

from app.api import HealthResource, BookListResource, BookResource
from app.db import teardown_db
from app.exceptions import NotFoundError

# Swagger/Flasgger configuration
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Books REST API",
        "description": "A REST API for managing a book collection",
        "version": "1.0.0",
    },
    "basePath": "/",
    "definitions": {
        "BookRequest": {
            "type": "object",
            "required": ["title", "author", "description", "status", "year_published"],
            "properties": {
                "title": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 100,
                    "example": "1984",
                },
                "author": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 100,
                    "example": "George Orwell",
                },
                "description": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 400,
                    "example": "A dystopian novel",
                },
                "status": {
                    "type": "string",
                    "enum": ["available", "borrowed"],
                    "example": "available",
                },
                "year_published": {
                    "type": "integer",
                    "minimum": 1,
                    "example": 1949,
                },
            },
        },
        "BookResponse": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "title": {"type": "string"},
                "author": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"},
                "year_published": {"type": "integer"},
            },
        },
    },
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

# Create Flask application
app = Flask(__name__)

# Initialize Flask-RESTful API
api = Api(app)

# Initialize Flasgger (Swagger UI)
swagger = Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

# Register resource routes
api.add_resource(HealthResource, "/api/health")
api.add_resource(BookListResource, "/api/books")
api.add_resource(BookResource, "/api/books/<string:book_id>")

# Manage the SQLAlchemy session lifecycle per request
app.teardown_appcontext(teardown_db)


@app.route("/")
def root():
    """Redirect root URL to Swagger UI."""
    return redirect("/apidocs/")


@app.errorhandler(HTTPException)
def handle_http_exception(exc):
    """Return JSON responses for HTTP errors instead of HTML."""
    return {"message": exc.description}, exc.code


@app.errorhandler(NotFoundError)
def handle_not_found(exc):
    """Return a 404 JSON response for NotFoundError exceptions."""
    return {"message": exc.message}, 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
