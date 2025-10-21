from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('<int:quiz_id>/session/', views.create_quiz_session, name='create_quiz_session'),
    path('join/<int:quiz_id>/', views.join_quiz, name='join_quiz'),
    path('play/<int:member_id>/', views.play_quiz, name='play_quiz'),
]



