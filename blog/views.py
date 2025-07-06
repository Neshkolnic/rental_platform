from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Post
from .forms import PostForm  # 👈 импорт формы отсюда

def is_blog_editor(user):
    return user.is_authenticated and user.role == 'blog_editor'

def index(request):
    posts = Post.objects.all()
    return render(request, 'blog/index.html', {'posts': posts})

@user_passes_test(is_blog_editor)
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('blog_index')
    else:
        form = PostForm()
    return render(request, 'blog/form.html', {'form': form, 'action': 'Создать'})

@user_passes_test(is_blog_editor)
def update_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('blog_index')
    return render(request, 'blog/form.html', {'form': form, 'action': 'Редактировать'})

@user_passes_test(is_blog_editor)
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog_index')
    return render(request, 'blog/delete_confirm.html', {'post': post})
