from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('search<str:mode>/keyword=<str:keyword>/', views.searchResult, name = 'searchResult'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('display/', views.display, name='display'),
    path('recommend/', views.recommend, name='recommend'),
    path('add_fav/', views.add_fav),
    path('click_fav/', views.click_fav)
]       