from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import PAGE_SIZE

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts.all()
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page,
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'form': form}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('index')
    return render(request, 'new.html', context)


@login_required
def post_edit(request, username, post_id):
    get_post = get_object_or_404(Post, author__username=username, pk=post_id)
    if get_post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=get_post)
    context = {
        'form': form, 'post': get_post
    }
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count_of_posts = paginator.count
    request_user = request.user
    if request_user.is_authenticated and request_user != author:
        following = Follow.objects.filter(
            user=request_user,
            author=author
        ).exists()
        context = {
            'author': author,
            'page': page,
            'count_of_posts': count_of_posts,
            'request_user': request_user,
            'following': following,

        }
        return render(request, 'profile.html', context)
    context = {
        'author': author, 'page': page,
        'count_of_posts': count_of_posts, 'request_user': request_user,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comment_list = post.comments.all()
    paginator = Paginator(comment_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    user = request.user
    user_profile = post.author
    form = CommentForm(request.POST or None,)
    context = {
        'author': user_profile, 'post': post,
        'page': page, 'user': user, 'form': form
    }
    if form.is_valid():
        # В шаблоне есть форма создания комментария,
        # чтобы не переходить на другую страницу.
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'post.html', context)


@login_required
def post_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None,)
    context = {'form': form}
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'comment.html', context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
    }
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    if request.user != following:
        Follow.objects.get_or_create(
            user=request.user,
            author=following,
        )
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    if request.user == follow.user:
        follow.delete()
        return redirect('profile', username)
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
