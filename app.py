from flask import Flask, render_template, request, session,url_for, redirect
from cassandra.cluster import Cluster
import requests
from pprint import pprint
#from jikanpy import Jikan
from werkzeug.security import generate_password_hash, check_password_hash
import os

cluster = Cluster(contact_points=['172.17.0.2'], port=9042)
s = cluster.connect()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


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

@app.route('/logout', methods = ['GET'])
def logout():
    session['username'] = ""
    session['isValid'] = False
    return redirect(url_for('index'))

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

#add to list and remove from list
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

@app.route('/<animeId>/removefromlist', methods = ['POST'])
def removefromlist(animeId):
    try:
        result = s.execute("delete from animedb.UserAnimeList where username = '{user}' and animeId = {aId};".format(user = session['username'], aId = animeId))
    except:
        print("error")
    return redirect(url_for('myList'))

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
            print(list)
        except:
            pass

    return render_template('myList.html',list=list)

#@app.route('/search', methods = ['POST'])
#def search():
#    return render_template('search.html')


if __name__ == '__main__':
    #app.run(host = '127.0.0.1:5000', debug=True)
    app.run(host='0.0.0.0', debug=True)
