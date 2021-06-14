from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("follow/", views.follow_index, name="follow_index"),
    path('group/<slug:slug>/', views.group_posts, name='group'),
    path('new/', views.new_post, name='new_post'),
    path(
        '<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        "<str:username>/follow/",
        views.profile_follow,
        name="profile_follow"
    ),
    path(
        "<str:username>/unfollow/",
        views.profile_unfollow,
        name="profile_unfollow"
    ),
    path(
        '<str:username>/<int:post_id>/',
        views.post_view,
        name='post'),
    path(
        '<str:username>/<int:post_id>/edit/',
        views.post_edit,
        name='post_edit'
    ),
]
