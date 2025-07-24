from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Post
from .forms import PostForm  # 👈 импорт формы отсюда


from django.shortcuts import render, get_object_or_404


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'blog/detail.html', {'post': post})


def is_blog_editor(user):
    return user.is_authenticated and user.role == 'blog_editor'

from django.db.models import Q

def index(request):
    query = request.GET.get('q', '').strip()  # если None — будет пустая строка
    posts = Post.objects.all().order_by('-created_at')

    if query:
        posts = posts.filter(title__icontains=query)

    paginator = Paginator(posts, 6)  # 6 постов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj, 'query': query})


@user_passes_test(is_blog_editor)
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Добавили request.FILES
        if form.is_valid():
            post = form.save()
            return redirect('blog_index')
    else:
        form = PostForm()
    return render(request, 'blog/form.html', {'form': form, 'action': 'Создать'})


@user_passes_test(is_blog_editor)
def update_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
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
