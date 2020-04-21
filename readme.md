# Cloud Computing (# ECS781P) Coursework (2019/2020)

This project is part of cloud computing course.

The project is an Anime shows web application based on AWS EC2 virtual Machine and uses Nginx Server, Flask framework for API development and Cassandra Database.

It contains 8 Apis and 2 external APIs from **Jikan**

https://jikan.docs.apiary.io/#reference/0/anime

The visitors can view Anime shows before registration and for users who have an account, they can add Anime shows to their list.

In each anime profile users will be able to see recommendations for related shows to what they are viewing.

I will be explaining database schema and database setup, then I will go through each API

## Database schema

The database contain four tables which are: 

### User Account:
This table contains:
- Username (Primary Key)
- Password
- isLocked

### User Details:
This table contains:
- Username (Primary Key)
- Gender
- Location
- Birthdate
- AnimeWatching
- AnimeCompleted
- AnimeOnHold
- AnimeDropped
- AnimePlanToWatch

### Anime List:
This table contains:
- AnimeId (Primary Key)
- Title
- ImageUrl
- Birthdate
- Type
- Source
- Episodes
- Status
- Airing
- AiredString
- Duration
- Rating
- Score
- ScoredBy
- Rank
- Popularity
- Background
- Premiered
- Licensor
- Studio
- Genre
- TrailerUrl

### User Anime List:
This table contains:
- Username (Primary Key)
- AnimeId (Primary Key)
- WatchedEpisodes
- MyScore
- Status

## Database Implementation

    #Create a directory
    ->sudo mkdir database
	->cd database
	
	#Install Docker
	->sudo apt-get install docker
	->sudo apt install docker.io
	
	#Pull Cassandra
	->sudo docker pull cassandra:latest
	
	#Run Docker with name animeDB
	->sudo docker run --name animeDB -p 9042:9042 -v /var/www/html/database:/var/lib/cassandra -d cassandra:latest

	# I have uploaded data to be inserted in the database the FileZilla

	#Copy Files to Docker
	->sudo docker cp AnimeList.csv animeDB:/home/AnimeList.csv
	->sudo docker cp UserAccounts.csv animeDB:/home/UserAccounts.csv
	->sudo docker cp UserAnimeList.csv animeDB:/home/UserAnimeList.csv
	->sudo docker cp UserList.csv animeDB:/home/UserList.csv

	#Enter command line for Cassandra
	->sudo docker exec -it animeDB cqlsh

	#Create table UserAccounts
	->CREATE TABLE animedb.userAccounts(id int, username text PRIMARY KEY, password text, isLocked boolean);

	#Copy data to the table
	->COPY animedb.userAccounts(id, username, password, isLocked) FROM '/home/UserAccounts.csv' WITH DELIMITER = ',' AND HEADER = TRUE;

	#Create table for userDetails
	->CREATE TABLE animedb.userDetails(id int, username text PRIMARY KEY, gender text, birthdate date, location text, AnimeWatching int, AnimeCompleted int, AnimeOnHold int, AnimeDropped int, AnimePlanToWatch int);

	#Copy data to the table
	->COPY animedb.userDetails(id, username, gender, birthdate, location, AnimeWatching, AnimeCompleted, AnimeOnHold, AnimeDropped, AnimePlanToWatch) FROM '/home/UserList.csv' WITH DELIMITER = ',' AND HEADER = TRUE;

	#Create table AnimeList
	->CREATE TABLE animedb.AnimeList(id int, animeId text PRIMARY KEY, title text, image_url text, type text, source text, episodes int, status text, airing boolean, airedString text, duration text, rating text, score float, scored_by int, rank float, popularity int, background text, premiered text, producer text, licensor text, studio text, genre text, trailerUrl text);

	#Copy data to the table
	->COPY animedb.AnimeList(id, animeId, title, image_url, type, source, episodes, status, airing, airedString, duration, rating, score, scored_by, rank, popularity, background, premiered, producer, licensor, studio, genre, trailerUrl) FROM '/home/AnimeList.csv' WITH DELIMITER = ',' AND HEADER = TRUE;

	#Create table for UserAnimeList
	->CREATE TABLE animedb.UserAnimeList(id int, username text, animeId int, myWatchedEpisodes int , myScore int, status int, PRIMARY KEY(username,animeId));

	#Copy data to the table
	->COPY animedb.UserAnimeList(id, username, animeId, myWatchedEpisodes, myScore, status) FROM '/home/UserAnimeList.csv' WITH DELIMITER = ',' AND HEADER = TRUE;

The data used is a subset of **myanimelist** downloaded from Kaggle and cleansed

[https://myanimelist.net/](https://myanimelist.net/)

## External APIs
I have used to external APIs within the APIs created to serve the web application

 1. To get info about anime and I have used it to get the poster of the anime as the posters URL in the database are outdated and no longer valid
 https://api.jikan.moe/v3/anime/{animeid}
 2. To get anime shows recommendation based on the anime profile you are viewing
 https://api.jikan.moe/v3/anime/{animeid}/recommendations

## Web Application APIs

- File Header
The file header include including libraries which will be used and defining objects

code:

    from flask import Flask,render_template, request, session,url_for, redirect
    from cassandra.cluster import Cluster import requests
    from pprint import pprint
    from werkzeug.security import generate_password_hash, check_password_hash
    import os
    cluster = Cluster(contact_points=['172.17.0.2'], port=9042)
    s = cluster.connect()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)

 - Root API
	 The Home page shows the latest anime shows from database and use external API to get the poster. However, in this web application I am controlling the Anime shows which is presented by hard coding anime shows id.
	**Note that you can access other anime shows which are not listed by changing the anime show id which is used as parameter in anime profile link**
	
code:

    @app.route('/', methods = ['GET'])
    def index():
	    myanimelist_url_template = "https://api.jikan.moe/v3/anime/{id}"
	    list =[]
	    result = s.execute("select animeId, title, score, premiered from animedb.AnimeList where animeId in ('7','8','15','16','17','19','20','21','22','26','27','28');")

	    for v in result:
	        url = myanimelist_url_template.format(id = v.animeid)
	        resp = requests.get(url)

	        if resp.ok:
	            anime_json = resp.json()
	        else:
	            print(resp.reasone)

	        try:
	            row = dict(animeId = v.animeid, url = anime_json['image_url'], title = v.title, score = round(v.score,2), premiered = v.premiered)
	            list.append(row)
	        except:
	            list.append("Error")
	            print("Error")
	            break

	    return render_template('index.html',list=list, animeId = v.animeid)

 - Login API
	 The API takes the inputs from user and look for a match of the username in the database, if there is a record it matches the hashed passwords to decide whether to let the user login or no. In case the user logged in session details will be stored and user will be redirected to the home page

code:

    @app.route('/login', methods = ['POST'])
    def login():
	    username = request.form['Username']
	    password = request.form['Password']
	    try:
	        result = s.execute("select username,password from animedb.userAccounts where username = '{}' allow filtering;".format(username))
	    except:
	        print("error")

	    if check_password_hash(result[0].password, password):
	        session['username'] = request.form['Username']
	        session['isValid'] = True
	        print(session['username'])

	    return redirect(url_for('index'))

 - Logout API
	 Logout API will clear all sessions and redirect the user to the home page

code:

    @app.route('/logout', methods = ['GET'])
    def logout():
	    session['username'] = ""
	    session['isValid'] = False
    return redirect(url_for('index'))

 - Register API
	This API takes prompted information from users to complete their registration and add their details into UserAccount and UserDetails table.

code:

    @app.route('/register', methods = ['POST'])
    def register():

	    username = request.form['Username']
	    password = request.form['Password']
	    gender = request.form['gender']
	    birthdate = request.form['BirthDate']

	    try:
	        useraccountIddb = s.execute("select max(id) from animedb.userAccounts;")
	        userdetailsIddb = s.execute("select max(id) from animedb.userDetails;")
	        useraccountId = int(useraccountIddb[0].system_max_id) + 1
	        userdetailsId = int(userdetailsIddb[0].system_max_id) + 1
	        result = s.execute("insert into animedb.userAccounts(id, username, password, isLocked) values({}, '{}', '{}' , False);".format(useraccountId,username,generate_password_hash(password)))
	        result2 = s.execute("insert into animedb.userDetails(id, username, gender, birthdate, location, AnimeWatching, AnimeCompleted, AnimeOnHold, AnimeDropped, AnimePlanToWatch) values({}, '{}', '{}', '{}', '', 0,0,0,0,0);".format(userdetailsId,username,gender,birthdate))
	    except:
	        print("error")

	    return redirect(url_for('index'))

 - Anime Profile API
	 The API takes anime id as parameter to provide anime details to the user from the database and it provide the poster and recommended anime shows using two external APIs

code:

    @app.route('/<animeId>/animeProfile', methods = ['GET'])
    def animeProfile(animeId):
	    myanimelist_url_template = "https://api.jikan.moe/v3/anime/{id}"
	    myanimelist_recommendation_url_template = "https://api.jikan.moe/v3/anime/{id}/recommendations"


	    result = s.execute("select title, episodes, status, rating, score, premiered, genre from animedb.AnimeList where animeId = '{}';".format(animeId))
	    if result:
	        url = myanimelist_url_template.format(id = animeId)
	        url2 = myanimelist_recommendation_url_template.format(id = animeId)
	        resp = requests.get(url)
	        resp2 = requests.get(url2)
	        if resp.ok:
	            anime_json = resp.json()
	            anime_rec_json = resp2.json()
	        else:
	            print(resp.reasone)
	            print(resp2.reasone)

	        poster = anime_json['image_url']
	        title = result[0].title
	        episodes = result[0].episodes
	        status = result[0].status
	        rating = result[0].rating
	        score = round(result[0].score,2)
	        premiered = result[0].premiered
	        genre = result[0].genre

        list= []
        for i in range(5):
            try:
                row = dict(url = anime_rec_json['recommendations'][i]['image_url'], title = anime_rec_json['recommendations'][i]['title'], recc= anime_rec_json['recommendations'][i]['recommendation_count'])
                list.append(row)
            except:
                list.append("Error")
                poster = "Error"
                break

	    return render_template('single.html', list = list, poster=poster, title=title, episodes=episodes, status=status, rating=rating, score=score, premiered=premiered, genre=genre,animeId=animeId)

 - Add to list API
	This API is for users who are using their account to enable them adding anime shows they prefer to their list so they can reference them later. The API checks if the user already have this anime in the list, if not it will be added otherwise nothing will happen

code:

    @app.route('/<animeId>/addtolist', methods = ['POST'])
    def addtolist(animeId):
	    try:
	        result = s.execute("select * from animedb.UserAnimeList where username = '{user}' and animeId = {aId};".format(user = session['username'], aId = animeId))
	        if result:
	            pass
	        else:
	            result = s.execute("insert into animedb.UserAnimeList(username,animeId,myWatchedEpisodes,myScore,status) values('{user}', {aId}, 0,0,0);".format(user = session['username'], aId = animeId))
	    except:
	        print("error")
	    return redirect(url_for('myList'))

 - Remove from list API
 This API is for users who are using their account to enable them removing anime shows from their list 

code:

    @app.route('/<animeId>/removefromlist', methods = ['POST'])
    def removefromlist(animeId):
	    try:
	        result = s.execute("delete from animedb.UserAnimeList where username = '{user}' and animeId = {aId};".format(user = session['username'], aId = animeId))
	    except:
	        print("error")
	    return redirect(url_for('myList'))

 - My List API
 This API is used for users who has account and logged in. First it checks from UserAnimeList table the anime shows the user added to his list and then uses AnimeList table to get the related information about the anime shows and finally it uses the external API to get anime posters for the anime shows in the list

code:

    @app.route('/myList', methods = ['GET'])
    def myList():
	    myanimelist_url_template = "https://api.jikan.moe/v3/anime/{id}"
	    list =[]
	    result = []
	    result_temp = s.execute("select animeId from animedb.UserAnimeList where username = '{user}';".format(user = session['username']))

	    if result_temp:
	        for animeid in result_temp:
	            try:
	                temp = s.execute("select animeId, title, score, premiered from animedb.AnimeList where animeId = '{id}';".format(id=animeid.animeid))
	                result.append(temp[0])
	            except:
	                pass

	    for v in result:
	        url = myanimelist_url_template.format(id = v.animeid)
	        resp = requests.get(url)

	        if resp.ok:
	            anime_json = resp.json()
	        else:
	            print(resp.reasone)

	        try:
	            row = dict(animeId = v.animeid, url = anime_json['image_url'], title = v.title, score = round(v.score,2), premiered = v.premiered)
	            list.append(row)
	                
	        except:
	            pass

	    return render_template('myList.html',list=list)


## Security

In this web application the following security measures where considered:

 1. Uses Hash-based Authentication
 2. Implementing user accounts and user access management where only registered users can make their lists and other users will not be able to see my list page and will not able to see buttons for adding and removing from list

