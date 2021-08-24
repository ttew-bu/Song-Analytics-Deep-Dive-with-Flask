import matplotlib
matplotlib.use('Agg')
import os
import re
from flask.wrappers import Response
import requests
import spotipy
import lyricsgenius
from io import BytesIO, StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Blueprint, render_template, current_app, request, Flask

app= Flask(__name__)

#define the client_id and client_secret

client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
genius_token= os.environ.get('genius_token')

client_credentials_manager = SpotifyClientCredentials(client_id,client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

genius = lyricsgenius.Genius(access_token=genius_token)

#Define the processes that occur on the landing page
@app.route('/', methods=['GET', 'POST'])

def homepage():

    #Create a blank list to store song names
    songs = []

    if request.method == "POST":
        results=sp.search(request.form.get('query'), type='track', limit=25)

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

@app.route('/song/<id>', methods=['GET'])

def get_song(id):

    #Define spotif yvariables 
    song = sp.track(id)
    analysis = sp.audio_features(id)

    #Create a list to iterate through artists
    artist_ids = []
    
    for artist in song['artists']:
        artist_ids.append(artist['id'])

    #Get the lyrics from Genius
    lyrics = genius.search_song(title=song['name'],artist=song['artists'][0]['name']).to_dict()
    re.sub('/n','<br>',lyrics['lyrics'])

    genres_raw = []

    for artist_id in artist_ids:
        art = sp.artist(artist_id)
        genres_raw += art['genres']

    #Create a list without duplicates for the genre information to display
    genres_complete=list(set(genres_raw))

    #create an empty dictionary of song 
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


    return render_template('song.html', lyrics=lyrics,song=song, genres=genres_complete, plot_url=plot_url)

if __name__ == '__main__':
    app.run()