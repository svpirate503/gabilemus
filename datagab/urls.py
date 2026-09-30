from django.urls import path

from . import views

urlpatterns = [
    path('', views.gabriel, name='gabriel'),
    path('contact/', views.contact, name='contact'),
]
