import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Blueprint, render_template, request, Flask
from azapi import AZlyrics
from sklearn import preprocessing
import pandas as pd
import json
import plotly
import plotly.express as px

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

@app.route('/about', methods=['GET'])

def about():
    return render_template('about.html')

@app.route('/models', methods=['GET'])

def models():
    return render_template('models.html')

@app.route('/song/<id>', methods=['GET'])

def get_song(id):

    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    #Define spotif yvariables 
    song = sp.track(id)
    analysis = sp.audio_features(id)

    df= pd.DataFrame(analysis[0],index=[0])

    df = df.loc[:,['danceability','energy','loudness',"speechiness",'acousticness','instrumentalness','liveness','valence','tempo']]


    #Create a list to iterate through artists
    artist_ids = []
    
    for artist in song['artists']:
        artist_ids.append(artist['id'])

    genres_raw = []

    for artist_id in artist_ids:
        art = sp.artist(artist_id)
        genres_raw += art['genres']

    #Create a list without duplicates for the genre information to display
    genres_complete=set(genres_raw)

    #Create a df and plot for the page
    df2 = pd.read_csv('spotipy_webapp/data/genres_41k.csv')

    df2 = df2.drop(columns=["track","artist","uri","target","genres",'mode','key','time_signature','chorus_hit','duration_ms','sections'])

    df2 = df2.append(df)

    scaler = preprocessing.MinMaxScaler()

    scaled_data = scaler.fit_transform(df2)

    scaled_df = pd.DataFrame(scaled_data, columns=df2.columns)

    placement_col = ["Dataset" for x in range(0,len(scaled_df)-1)]

    placement_col.append(song['name'])

    scaled_df['placement'] = placement_col

    fig = px.box(scaled_df,y=scaled_df.columns, points=False,color="placement")

    fig.update_layout(title="Song Analytics View",title_x=0.5,yaxis_title="Normalized Value",xaxis_title="Song Features (from Spotify)",font=dict(
        family="Verdana, Sans-serif",
        size=16,color="black"))

    

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)  

    return render_template('song.html', df=df, song=song, genres=genres_complete, graph=graphJSON)

@app.route('/song/<id>/lyricanalysis', methods=['GET'])

def lyrics_tab(id):

    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    #Define spotify variables 
    track = sp.track(id)
    id = track['id']
    singer = track['artists'][0]['name']
    track_name = track['name']

    api = AZlyrics()

    api.artist = singer
    api.title= track_name
    lyrics = api.getLyrics()

    return render_template('wordreview.html',lyrics=lyrics,id=id)

if __name__ == '__main__':
    app.run()