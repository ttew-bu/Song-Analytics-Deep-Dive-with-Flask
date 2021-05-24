from flask import Flask 

from .app import main

#Create method to create application from settings file
def create_app():

    #Define the application using Flask 
    app = Flask(__name__)

    #Register the main blueprint for page routing 
    app.register_blueprint(main)

    print(app.name)

    #return our application
    return app

