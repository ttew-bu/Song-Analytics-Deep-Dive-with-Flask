import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Blueprint, render_template, current_app, request, Flask

from sklearn import preprocessing

import plotly
import plotly.express as px

import pandas as pd
import json

app= Flask(__name__)

#define the client_id and client_secret

client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')

client_credentials_manager = SpotifyClientCredentials(client_id,client_secret)

#Define the processes that occur on the landing page
@app.route('/', methods=['GET', 'POST'])

def homepage():

    #Create a blank list to store song names
    songs = []

    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

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

    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    #Define spotif yvariables 
    song = sp.track(id)
    analysis = sp.audio_features(id)
    features = []

    df= pd.DataFrame()

    df['energy'] = ''*df.shape[0]
    df['loudness'] = ''*df.shape[0]
    df['speechiness'] = ''*df.shape[0]
    df['valence'] = ''*df.shape[0]
    df['liveness'] = ''*df.shape[0]
    df['tempo'] = ''*df.shape[0]
    df['danceability'] = ''*df.shape[0]
    df['acousticness'] = ''*df.shape[0]
    df['acousticness'] = ''*df.shape[0]

    for i in range (0,df.shape[0]):    
        df.loc[i,'energy'] = features[0]['energy']
        df.loc[i,'speechiness'] = features[0]['speechiness']
        df.loc[i,'liveness'] = features[0]['liveness']
        df.loc[i,'loudness'] = features[0]['loudness']
        df.loc[i,'danceability'] = features[0]['danceability']
        df.loc[i,'tempo'] = features[0]['tempo']
        df.loc[i,'valence'] = features[0]['valence']
        df.loc[i,'acousticness'] = features[0]['acousticness']
        df.loc[i,'instrumentalness'] = features[0]['instrumentalness']


    #Create a list to iterate through artists
    artist_ids = []
    
    for artist in song['artists']:
        artist_ids.append(artist['id'])

    genres_raw = []

    for artist_id in artist_ids:
        art = sp.artist(artist_id)
        genres_raw += art['genres']

    #Create a list without duplicates for the genre information to display
    genres_complete=list(set(genres_raw))


    #Create a df and plot for the page
    df2 = pd.read_csv('spotipy_webapp/data/genres_41k.csv')

    df2 = df2.drop(columns=["track","artist","uri","target","genres",'mode','key','time_signature','chorus_hit','duration_ms','sections'])

    df2.append(df)

    scaler = preprocessing.MinMaxScaler()

    scaled_data = scaler.fit_transform(df2)

    scaled_df = pd.DataFrame(scaled_data, columns=df2.columns)

    fig = px.box(scaled_df,y=scaled_df.columns, points=False)

    fig.update_layout(title="Song Analytics View",title_x=0.5,yaxis_title="Normalized Value",xaxis_title="Song Features (from Spotify)",font=dict(
        family="Verdana, Sans-serif",
        size=16))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)  

    return render_template('song.html', song=song, genres=genres_complete, graph=graphJSON)

if __name__ == '__main__':
    app.run()