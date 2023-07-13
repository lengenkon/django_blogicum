from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"]
        return first_name.split()[0]


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
