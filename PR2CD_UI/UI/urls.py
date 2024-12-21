from django.urls import path

from . import views

app_name = "UI"

urlpatterns = [
    path('', views.index, name='index'),
    path('submit', views.submit_req, name="submit"),
    path('diagram',views.diagram, name="diagram"),
    path('about',views.about, name="about"),
    path('contact', views.contact, name="contact")

]
