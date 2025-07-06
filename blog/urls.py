from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='blog_index'),
    path('create/', views.create_post, name='blog_create'),
    path('<int:post_id>/edit/', views.update_post, name='blog_edit'),
    path('<int:post_id>/delete/', views.delete_post, name='blog_delete'),
]
