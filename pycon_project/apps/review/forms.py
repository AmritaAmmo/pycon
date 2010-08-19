from django import forms

from review.models import Review, Comment


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["vote", "comment"]


class ReviewCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]


class SpeakerCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
