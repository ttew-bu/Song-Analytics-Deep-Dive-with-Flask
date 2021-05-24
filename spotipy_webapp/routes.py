import matplotlib
matplotlib.use('Agg')
from os import error
from flask.wrappers import Response
import requests
import spotipy
from io import BytesIO, StringIO
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import base64
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Blueprint, render_template, current_app, request
from .config import client_secret, client_id

#define the client_id and client_secret

client_credentials_manager = SpotifyClientCredentials(client_id,client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#Define the main
main = Blueprint('main',__name__)

#Define the processes that occur on the landing page
@main.route('/', methods=['GET', 'POST'])

def homepage():

    #Create a blank list to store song names
    songs = []

    if request.method == "POST":
        results=sp.search(request.form.get('query'), type='track', limit=25)
        
        #Test to see that the list of tracks routes correctly 
        # print(results['tracks']['items'])
        # print(len(results['tracks']['items']))


        #Iterate through song ids and add them to the ids list
        for instance in range(len(results['tracks']['items'])):

            #Create a dictionary of all relevant data for the model and html page to use
            song_data = {
            'name': results['tracks']['items'][instance]['name'],
            'id': results['tracks']['items'][instance]['id'],
            'cover': results['tracks']['items'][instance]['album']['images'][0]['url']
            }

            #Add each song to the dictionary
            songs.append(song_data)
    
    
    return render_template('homepage.html', foob=songs)

@main.route('/song/<id>', methods=['GET'])

def get_song(id):

    song = sp.track(id)
    analysis = sp.audio_features(id)

    song_dict = dict()

    analysis_components = sorted(analysis[0].items())

    for key,value in analysis_components:
        song_dict.setdefault(key, []).append(value)


    #Define a list of useless variables we can drop 

    drop_list = ['analysis_url', 'track_href','type','uri','id','duration_ms']
    for var in drop_list:
        del song_dict[var]
    

    keys =list(song_dict.keys())
    val_list = list(song_dict.values())
    values = [x[0] for x in val_list]

    print(keys)
    print(values)

    #Create the plot 
    fig = plt.figure()
    ax = fig.subplots()
    sns.set_theme()
    ax.bar(x=keys,height=values)
    ax.set_xticklabels(keys)
    ax.set_title('Song Features')

    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

    #Create a PNG image of the plot
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches="tight")

    #Convert PNG to Byte String (Base64)
    plot_url = base64.b64encode(img.getbuffer()).decode('utf8')
    

    return render_template('song.html', song=song, plot_url=plot_url)





