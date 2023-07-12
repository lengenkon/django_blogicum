from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()


class HomePage(ListView):
    model = Post
    paginate_by = 10
    template_name = "blog/index.html"

    def get_queryset(self):
        return (
            Post
            .objects
            .select_related('category', 'location', 'author')
            .annotate(comment_count=Count('comments'))
            .filter(
                pub_date__lte=timezone.now(),
                is_published=True,
                category__is_published=True
            )
            .order_by('-pub_date')
        )


class UserListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = 10
    ordering = '-pub_date'

    def get_queryset(self):
        author = get_object_or_404(
            User.objects.filter(
                username=self.kwargs['username_slug']
            )
        )
        if author == self.request.user:
            return Post.objects.select_related(
                'category', 'location', 'author',
            ).filter(
                author=author
            ).order_by(
                '-pub_date'
            ).annotate(
                comment_count=Count('comments'),
            )
        return Post.objects.select_related(
            'category', 'location', 'author',
        ).filter(
            author=author,
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comments'),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User.objects.filter(
                username=self.kwargs['username_slug'],
            )
        )
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user and instance.is_published is False:
            raise Http404
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        context['form'] = post
        return context

    def get_success_url(self):
        return reverse('blog:index')


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            Post
            .objects
            .annotate(comment_count=Count('comments'))
            .select_related('category', 'location', 'author')
            .filter(
                category__slug=self.kwargs['category_slug'],
                pub_date__lte=timezone.now(),
                is_published=True,
                category__is_published=True
            )
            .order_by('-pub_date',)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author_id = self.request.user.id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={"username_slug": self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('blog:post_detail', kwargs={"pk": pk})

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.pk)
        return super().dispatch(request, *args, **kwargs)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = (
        'first_name',
        'last_name',
        'username',
        'email'
    )
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_success_url(self):
        return reverse('blog:edit_profile',
                       kwargs={'username': self.request.user.username})

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(User, username=self.kwargs['username'])
        if instance.username != request.user.username:
            return redirect('blog:profile', instance.username)
        return super().dispatch(request, *args, **kwargs)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)


class CommentUpdateView(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = "blog/comment.html"
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post.pk)
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})
