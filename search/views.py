from os import stat
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.template import loader
import time
from django.shortcuts import redirect
from django.db import models
from .models import User, Favorite
# Create your views here.
import json
import pickle
from whoosh.index import open_dir
import re
import datetime
import pprint
ix = open_dir("./index")
from whoosh.qparser import QueryParser, OrGroup, NotGroup, attach
from whoosh.query import And, Or, Term, Not
parser1 = QueryParser("content", ix.schema, group=OrGroup)
parser2 = QueryParser("title", ix.schema, group=OrGroup)
parser3 = QueryParser("author", ix.schema, group=OrGroup)
searcher = ix.searcher()



def load_article_list():
    with open('./mock_data/Papers.pkl', 'rb') as f:
        tmp = pickle.load(f)
    return tmp

def handleAbstract(article, keyword):
    
    text = article["abstract"]

    text = text.split(" ")
    keywords = keyword.split(" ")
    match_pos = []
    for i, word in enumerate(text):
        if word in keywords:
            match_pos.append(i)
    match_pos = match_pos[:10]
    print(match_pos)
    article["abstract"] = " ".join(text[:100]) + "..."


article_list = load_article_list()

def index(request):
    status = request.COOKIES.get('is_login')
    startTime = time.time()

    print(status)
    status = (status is not None)
    if dict(request.GET).get('keyword') == None or request.GET['keyword'] == "":
        template = loader.get_template('search/index.html')
        return HttpResponse(template.render({"status": status}, request))
    else:
        return searchResult(request, request.GET['keyword'])



def searchResult(request, mode, keyword):
    status = request.COOKIES.get('is_login')  # 通过cookie看是否登录。其实应该做的是5min不更新就自动登出
    startTime = time.time()

    print(status)
    status = (status is not None)
    print('status', status)

    fav_list = []
    if status:
        username = request.COOKIES.get("username")
        favorite_list = Favorite.objects.filter(username=username).all()
        
        fav_list = [fav.paperid for fav in favorite_list]
    
    page = int(request.GET['page'])
    begin = (page - 1) * 10


    print(keyword)
    query1 = parser1.parse(keyword)
    query2 = parser2.parse(keyword)
    query3 = parser3.parse(keyword)
    
    query = Or([query1, query2, query3])

    print('query', query)
    from whoosh import highlight
    from whoosh.analysis.analyzers import StandardAnalyzer
    # results = searcher.search(query)

    if mode == "All":
        results = searcher.search_page(query, page, 10)
    elif mode == "ByTime":
        results = searcher.search_page(query, page, 10, sortedby="year", reverse=True)
    elif mode == "ByCite":
        results = searcher.search_page(query, page, 10, sortedby="citation", reverse=True)
    
    
    my_fr = highlight.ContextFragmenter(maxchars=100, surround=150, charlimit=32768)
    results.results.fragmenter = my_fr
    ret_data = []
    for a in results:
        obj = {}
        id = int(a["id"])
        print('id', id)
        abs = a.highlights("content", top=10)
        obj['abstract'] = abs if len(abs) > 0 else a["content"][:200]
        abs = obj['abstract'].replace('<b', '<span').replace('</b', '</span')
        obj['abstract'] = re.sub(r'class="match term\d*"', 'style="color:red"', abs)

        if not obj["abstract"].startswith(a["content"][:20]):
            obj["abstract"] = "..." + obj["abstract"]

        if not obj["abstract"].endswith(a["content"][-20:]):
            obj["abstract"] = obj["abstract"] + "..."

        obj["title"] = a.highlights("title")
        if len(obj["title"]) == 0:
            obj["title"] = a["title"]

        obj["title"] = obj["title"].replace('<b', '<span').replace('</b', '</span')
        obj["title"] = re.sub(r'class="match term\d*"', 'style="color:red"', obj["title"])



        obj["id"] = id
        obj["favorite"] = True if id in fav_list else False
        obj["url"] = article_list[id]["URL"]
        obj["author"] = a.highlights("author")
        if len(obj["author"]) == 0:
            obj["author"] = a["author"]

        obj["author"] = obj["author"].replace('<b', '<span').replace('</b', '</span')
        obj["author"] = re.sub(r'class="match term\d*"', 'style="color:red"', obj["author"])

        obj["citation"] = article_list[id]["citation"]
        obj["type"] = article_list[id]["type"].split(":")[0]
        obj["year"] = article_list[id]["year"]

        ret_data.append(obj)
    num = len(results)
    
    maxPage = (num+9) // 10
    if (page < 6):
        allpage = [i for i in range(1, 12) if i <= maxPage]
    else:
        allpage = [i for i in range(page - 5, page + 6) if i <= maxPage]
    
    endTime = time.time()
    delTime = str((endTime - startTime)/2)[0:5]
    
    
    context = {'num': num, 'list' : ret_data, 'keyword' :  keyword,
                            'page':page, 'maxPage':maxPage, 'allpage':allpage, 'time':delTime, 'status': status}

    if mode == "All":
        context['modeAll'] = True
    elif mode == 'ByTime':
        context['modeTime'] = True
    elif mode == 'ByCite':
        context['modeCite'] = True


    return render(request, 'search/searchResult.html', context=context)


def login(request):
    if request.method == "GET":
        template = loader.get_template('search/login.html')
        return HttpResponse(template.render({}, request))
    else:
        if request.POST.get("username"):
            ##login
            username = request.POST.get("username")
            password = request.POST.get("pwd")
            print(username, password)

            user_obj = User.objects.filter(username=username, password=password).first()

            if not user_obj:
                return redirect("/login/")
            else:
                rep = redirect("/index/")
                rep.set_cookie("is_login", True)
                rep.set_cookie("username", username)
                return rep 
        else:
            ##register
            username = request.POST.get("register-username")
            password = request.POST.get("register-pwd")
            
            user_obj = User.objects.filter(username=username).first()
            if user_obj:
                return redirect("/login/")
            
            user = User()
            user.username = username
            user.password = password
            user.save()
        
            rep = redirect("/index/")
            rep.set_cookie("is_login", True)
            rep.set_cookie("username", username)
            return rep 
        

def logout(request):
    print('logout')
    rep = redirect('/index/')
    rep.delete_cookie("is_login")
    rep.delete_cookie("username")
    return rep


def display(request):
    status = request.COOKIES.get('is_login')
    status = (status is not None)
    if not status:
        return redirect('/login/')


    username = request.COOKIES.get("username")
    favorite_list = Favorite.objects.filter(username=username).all()
    fav_list = [fav.paperid for fav in favorite_list]
    page = int(request.GET['page'])
    begin = (int(page) - 1) * 20
    articleList = [article_list[i] for i in fav_list][begin:begin+20]
    ret_data = []
    for a in articleList:
        obj = {}
        id = int(a["id"])
        obj['abstract'] = ' '.join(a["abstract"].split(' ')[:100]) + '...'
        obj["title"] = a["title"]
        obj["id"] = id
        obj["favorite"] = True if id in fav_list else False
        obj["url"] = article_list[id]["URL"]
        obj["author"] = a["authors"]

        obj["citation"] = article_list[id]["citation"]
        obj["type"] = article_list[id]["type"].split(":")[0]
        obj["year"] = article_list[id]["year"]

        ret_data.append(obj)
    num = len(articleList)
    maxpage = (num + 19) // 20
    allpage = [i for i in range(page-5, page+6) if 0 < i and i <= maxpage]
    return render(request, 'search/display.html', {'page' : int(page), 'list' : ret_data, 'num':num, 'allpage':allpage, 'max':maxpage})

def random_recommend(request):
    status = request.COOKIES.get('is_login')
    status = (status is not None)
    import random 

    idx = list(range(len(article_list)))
    random.shuffle(idx)
    idx = idx[:20]
    articleList = [article_list[i] for i in idx]
    print('random recommend')
    ret_data = []
    for a in articleList:
        obj = {}
        id = int(a["id"])
        obj['abstract'] = ' '.join(a["abstract"].split(' ')[:100]) + '...'
        obj["title"] = a["title"]
        obj["id"] = id
        obj["favorite"] = False
        obj["url"] = article_list[id]["URL"]
        obj["author"] = a["authors"]

        obj["citation"] = article_list[id]["citation"]
        obj["type"] = article_list[id]["type"].split(":")[0]
        obj["year"] = article_list[id]["year"]

        ret_data.append(obj)
    num = len(articleList)
    type = 'random'
    return render(request, 'search/recommend.html', {'list' : ret_data, 'num':num, 'status': status, 'random': True})

def recommend(request):
    status = request.COOKIES.get('is_login')
    status = (status is not None)
    if not status:
        return random_recommend(request)



    username = request.COOKIES.get("username")
    favorite_list = Favorite.objects.filter(username=username).all()
    fav_list = [fav.paperid for fav in favorite_list]
    if len(fav_list) == 0:
        return random_recommend(request)
    
    print(fav_list)
    ## get recommend
    import numpy as np
    from collections import defaultdict
    score = defaultdict(float)
    for i in fav_list:
        s_dict = article_list[i]["score"]
        for k in s_dict:
            score[k] += s_dict[k]
    tmp = [(i, score[i]) for i in score]
    tmp = sorted(tmp, key=lambda x: -x[1])
    tmp = tmp[:100]
    print(tmp)


    articleList = [article_list[id] for id, _ in tmp if id not in fav_list and id < len(article_list)][:20]

    ret_data = []
    for a in articleList:
        obj = {}
        id = int(a["id"])
        obj['abstract'] = ' '.join(a["abstract"].split(' ')[:100]) + '...'
        obj["title"] = a["title"]
        obj["id"] = id
        obj["favorite"] = False
        obj["url"] = article_list[id]["URL"]
        obj["author"] = a["authors"]

        obj["citation"] = article_list[id]["citation"]
        obj["type"] = article_list[id]["type"].split(":")[0]
        obj["year"] = article_list[id]["year"]

        ret_data.append(obj)


    num = len(articleList)
    return render(request, 'search/recommend.html', {'list' : ret_data, 'num':num, 'status': status, 'random': False})



def add_fav(request):
    status = request.COOKIES.get('is_login')
    
    if not status:
        return redirect('/login/')
    username = request.COOKIES.get("username")
    id = request.GET['id']
    fav = Favorite.objects.filter(username=username, paperid=id).first()
    if fav: return HttpResponse() 
    
    fav = Favorite()
    fav.username = username
    fav.paperid = id
    fav.save()
    return HttpResponse()

def cancle_fav(request):
    status = request.COOKIES.get('is_login')
    
    if not status:
        return redirect('/login/')
    username = request.COOKIES.get("username")
    id = request.GET['id']

    fav = Favorite.objects.filter(username=username, paperid=id).all()
    if fav:
        for f in fav:
            f.delete()

    return HttpResponse()

def click_fav(request):
    status = request.COOKIES.get('is_login')
    
    if not status:
        return redirect('/login/')
    username = request.COOKIES.get("username")
    id = request.GET['id']

    fav = Favorite.objects.filter(username=username, paperid=id).all()
    if fav:
        for f in fav:
            f.delete()
    else:
        fav = Favorite()
        fav.username = username
        fav.paperid = id
        fav.save()
    return HttpResponse()