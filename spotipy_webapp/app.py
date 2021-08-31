import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import render_template, request, Flask
import azapi
import lyricsgenius
from sklearn import preprocessing
import pandas as pd
import json
import numpy as np
import plotly
import plotly.express as px
import pickle
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize

#Define the application within Flask
app= Flask(__name__)

#define the client_id and client_secret for spotify API access
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
genius_token = os.environ.get('genius_token')

#Instantiate the credentials manager to make API calls
client_credentials_manager = SpotifyClientCredentials(client_id,client_secret)

#Define the processes that occur on the landing page
@app.route('/', methods=['GET', 'POST'])


def homepage():
    '''This function governs the actions that occur on the home/search page for the app including Spotify calls and data attribute collection'''

    #Create a blank list to store song names
    songs = []

    #Use spotify API client to create an object to perform calls (via Python methods) to the api
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    #If the search bar is clicked and a post request is sent, do this
    if request.method == "POST":

        #Define a list of results from the Spotify search using the query taken in via HTML input
        results=sp.search(request.form.get('query'), type='track', limit=25)

        #Iterate through song ids and add them to the ids list
        for instance in range(len(results['tracks']['items'])):

            #Create a dictionary of all relevant data for the model and html page to use
            song_data = {
            'name': results['tracks']['items'][instance]['name'],
            'id': results['tracks']['items'][instance]['id'],
            'cover': results['tracks']['items'][instance]['album']['images'][0]['url'],
            'main artist': results['tracks']['items'][instance]['artists'][0]['name']
            }

            #Add each song to the dictionary
            songs.append(song_data)
    
    #Return the template with variable songs represented by search_results in the html
    return render_template('homepage.html', search_results=songs)

@app.route('/about', methods=['GET'])

def about():
    '''Return the plain HTML page for the about section of the webapp'''
    return render_template('about.html')

@app.route('/models', methods=['GET'])

def models():
    '''Return the plain HTML page for the models section of the webapp'''
    return render_template('models.html')

@app.route('/song/<id>', methods=['GET'])


def get_song(id):
    '''Return the HTML page for one search result and song character analysis'''

    ##FLOW FOR THE BASIC SONG INFORMATION##
    #Instantiate Spotify again
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    #Define spotify variables 
    song = sp.track(id)
    analysis = sp.audio_features(id)

    #Create a dataframe from the song features so it can be highlighted on the page
    df= pd.DataFrame(analysis[0],index=[0])

    #Select only the relevant columns from the dataframe and redefine the variable df
    df = df.loc[:,['danceability','energy','loudness',"speechiness",'acousticness','instrumentalness','liveness','valence','tempo']]

    #Create a list to iterate through artists and gather their information
    artist_ids = []
    
    #For artist credited on the song, keep the song ID
    for artist in song['artists']:

        #add artist ids to the list
        artist_ids.append(artist['id'])

    #Create a variable to store each of the genres associated with an artist
    genres_raw = []

    #Iterate through each artist id in the list to get the genres associated with the song
    for identifier in artist_ids:
        
        #create an object for the artist based on the ID
        art = sp.artist(identifier)

        #add the genres to the raw genres list
        genres_raw += art['genres']

    #Create a list without duplicates for the genre information to display
    genres_complete=set(genres_raw)


    ##FLOW FOR CREATING THE ANALYSIS CHART##
    #Create a df and plot for the page based on the adapted billboard dataset
    df_chart = pd.read_csv('spotipy_webapp/data/genres_41k.csv')

    #drop the irrelevant columns from the chart so it can be used in visualization
    df_chart = df_chart.drop(columns=["track","artist","uri","target","genres",'mode','key','time_signature','chorus_hit','duration_ms','sections'])

    #Add the new song to the df for the chart 
    df_chart = df_chart.append(df)

    #Instantiate a scaler so that the chart is a bit more understandable
    scaler = preprocessing.MinMaxScaler()

    #Scale df_chart and store the data in a variable
    scaled_data = scaler.fit_transform(df_chart)

    #Convert the df_chart to a scaled variable ready to be put into the chart
    scaled_df = pd.DataFrame(scaled_data, columns=df_chart.columns)

    #Create a column to differentiate the actual song from the dataset, which is the last index of the dataset
    placement_col = ["Sample" for x in range(0,len(scaled_df)-1)]

    #Add the song name to the last object in the column so that the song name can be pulled
    placement_col.append(song['name'])

    #Add the placement_col list to the new dataframe as a new column
    scaled_df['placement'] = placement_col

    #Use plotly express to create a boxplot differentiating on the dataset v. the song in question
    fig = px.box(scaled_df,y=scaled_df.columns, points=False,color="placement",color_discrete_map={song['name']: '#F4A896','Sample':'grey'})

    #Add chart titles and formatting
    fig.update_layout(paper_bgcolor="#358597",plot_bgcolor='white',title="Song Analytics View",legend_title="Legend",title_x=0.5,yaxis_title="Normalized Value",xaxis_title="Song Features (from Spotify)", font=dict(
        family="Georgia, Serif",
        size=16,color="white"))

    
    #Convert the figure to json format so that it can be loaded in the html file
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)  

    #Return the template and create variables for the items to be displayed on the html page
    return render_template('song.html', df=df, song=song, genres=genres_complete, graph=graphJSON)


@app.route('/song/<id>/lyricanalysis', methods=['GET'])
def lyrics_tab(id):
    '''Create the data to display the lyrics and instantiate the VADER sentiment analysis tool'''
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    #Define spotify variables 
    track = sp.track(id)
    id = track['id']
    singer = track['artists'][0]['name']
    track_name = track['name']

    #Use the Genius API 
    genius = lyricsgenius.Genius(access_token=genius_token)

    genius_results = genius.search_song(track_name,singer)
        #If blank query, create a null and a continue running down the list
    if genius_results == None or genius_results == np.nan:
        lyrics = np.nan

    else:
        result_artist = str(genius_results.primary_artist.name)

        if result_artist in singer:
            lyrics = genius_results.lyrics
        else:
            lyrics=np.nan

    #sub the bracket expressions via regex, these are commonly something like [(Shakira) Verse 1:] which are not lyrics
    analysis_lyrics = re.sub(r"[\[].*?[\]]", "", lyrics)

    analysis_lyrics = analysis_lyrics.replace("EmbedShare URLCopyEmbedCopy","")

    #Add html elements to create lyrics to display
    display_lyrics = analysis_lyrics.split('\n')

    #Tokenize lyrics so they can be put into the VADER object
    tokenized_lyrics = word_tokenize(analysis_lyrics)

    #Instantiate VADER for sentiment intensity analysis
    sid = SentimentIntensityAnalyzer()

    #Create lists for positive words and negative words, which will be passed in to be highlighted
    positive_words=[]
    negative_words=[]

    #Iterate over words in the song and see if they're positive or negative based on polarity score
    for word in tokenized_lyrics:
        if (sid.polarity_scores(word)['compound']) >= 0.05:
            positive_words.append(word)
        elif (sid.polarity_scores(word)['compound']) <= -0.05:
            negative_words.append(word)

        #If it is not positive or negative, then ignore and continue working through the song
        else:
            continue

    vader_score = sid.polarity_scores(analysis_lyrics)

    #load the model and vector from memory
    model = pickle.load(open('spotipy_webapp/model_tools/genre_pred_model.pickle', 'rb'))
    vect = pickle.load(open('spotipy_webapp/model_tools/vectorizer.pickle', 'rb'))
    #sub line breaks out via regex
    processed_lyrics = re.sub(r"\n+", " ", analysis_lyrics)

    #sub all other punctuation out via regex
    processed_lyrics = re.sub(r'[^\w\s]', '', processed_lyrics)

    #Convert all upper-case words to lower-case
    processed_lyrics = [processed_lyrics.lower()]
    vectorized_lyrics = vect.transform(processed_lyrics).toarray()
    #predict
    prediction = model.predict(vectorized_lyrics)[0]

    return render_template('sentiment_analysis.html',id=id,prediction=prediction,song=track_name,singer=singer,lyrics=display_lyrics,positive_words=positive_words,negative_words=negative_words,vader_score=vader_score)
        
#Build out error cases based on early tests so the app runs smoothly.
@app.errorhandler(TypeError)
def error():
    '''serve up error page if type error'''

    return render_template('error.html')

@app.errorhandler(Exception)
def error():
    '''serve up error page if Exception'''

    return render_template('error.html')
if __name__ == '__main__':
    app.run()