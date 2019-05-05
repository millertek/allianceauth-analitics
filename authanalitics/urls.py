from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'authanalitics'

urlpatterns = [
    url(r'^$', views.outputcsv, name='outputcsv'),
]
