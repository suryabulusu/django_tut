from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Survey(models.Model):
    """Survey created by user"""
    title = models.CharField(max_length = 64) # default
    is_active = models.BooleanField(default = False)
    creator = models.ForeignKey(User, on_delete = models.CASCADE) # what
    created_at = models.DateTimeField(default = timezone.now)

class Question(models.Model):
    """a text field, and who created it / which survey it belongs to"""
    survey = models.ForeignKey(Survey, on_delete = models.CASCADE)
    prompt = models.CharField(max_length = 128) # better if we take from user
    # or set in some settings page

class Option(models.Model):
    """"option choice to some question"""
    question = models.ForeignKey(Question, on_delete = models.CASCADE)
    text = models.CharField(max_length = 128)

class Submission(models.Model):
    """to which survey is it submitted"""
    survey = models.ForeignKey(Survey, on_delete = models.CASCADE)
    created_at = models.DateTimeField(default = timezone.now)
    is_complete = models.BooleanField(default = False) # what's the purpose of this
    # i suppose these things would spring up only after writing some views
    # especially boolean

class Answer(models.Model):
    """"Answer to question / which submission does it belong to; and the chosen option"""
    submission = models.ForeignKey(Question, on_delete = models.CASCADE)
    option = models.ForeignKey(Option, on_delete = models.CASCADE)