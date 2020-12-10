# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
        
    path(route = '',
          view  = views.home, 
          name='home'),
    
    # This is the built-in admin site that django provides
    path(route = 'admin/', 
         view = admin.site.urls,
         name = 'admin'),
    
    # this is profile system with login/logout
    path(route = 'accounts/',
         view = include('accounts.urls'),
         name = 'accounts'),
    
    # path(route = 'exam/',
    #      view = include('exam.urls'),
    #      name = 'exam'),
    
]
