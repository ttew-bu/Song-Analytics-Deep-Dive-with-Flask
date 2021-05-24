from flask import Flask 

from .routes import main

#Create method to create application from settings file
def create_app(config_file='settings.py'):

    #Define the application using Flask 
    app = Flask(__name__)

    #Configure the application from the predefined settings.py file 
    app.config.from_pyfile(config_file)

    #Register the main blueprint for page routing 
    app.register_blueprint(main)

    app.config.from_pyfile('config.py')

    #return our application
    return app

