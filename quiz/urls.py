from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('edit/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('join/<int:quiz_id>/', views.join_quiz, name='join_quiz'),
    path('play/<int:member_id>/', views.play_quiz, name='play_quiz'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]



