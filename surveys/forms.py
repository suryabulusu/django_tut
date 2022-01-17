from django import forms

from .models import Answer, Survey, Question, Option

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ["title"] 

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["prompt"]

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ["text"]

# the above forms are straightforward .. input/output stuff
# but answer.. it has the multiple-option-choose-one-out-of-them thing
class AnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = kwargs.pop("options")
        choices = {(o.pk, o.text) for o in options} # foreign key, text
        # why exactly do this.. what additional info does options contain
        # do a print(options)
        option_field = forms.ChoiceField(choices = choices, widget = forms.RadioSelect, required = False)
        # option_field = options displayed to user
        self.fields["option"] = option_field 
        # for field in forms: {{field.label_tag}} (option), {{field}} (option_field radio buttons) are displayed
        # why give o.pk to options?!!

# AnswerFormSet is different from BaseFormSet
# how? don't know! tricky part
class BaseAnswerFormSet(forms.BaseFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index) # similar function as base class
        kwargs["options"] = kwargs["options"][index]
        return kwargs