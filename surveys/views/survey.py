from django.db import transaction
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory # for multiple options
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from ..models import Option, Survey, Question, Answer, Submission
from ..forms import SurveyForm, QuestionForm, OptionForm, AnswerForm, BaseAnswerFormSet

@login_required # you only see survey list if you are logged in
def survey_list(request):
    """returns a list of surveys"""
    surveys = Survey.objects.filter(creator = request.user).order_by("-created_at").all() # what does .all() do?
    return render(request, "survey_tmpl/list.html", {"surveys": surveys})

@login_required
def detail(request, pk):
    """user can view onclick the survey
    args:
    request: Request by the user
    pk: Foreign key of the survey / identifier of the survey
    """
    try:
        # get me the related questions and answers ?! 
        # how do you that? -- coz the pk of survey has been linked?!
        survey = Survey.objects.prefetch_related("question_set__option_set").get(
            pk = pk, creator = request.user, is_active = True
        )
    except Survey.DoesNotExist:
        raise Http404()

    questions = survey.question_set.all()

    # calculations
    for question in questions:
        # get the linked options
        option_pks = question.option_set.values_list("pk", flat = True)
        # get all answers linked to the option
        total_answers = Answer.objects.filter(option_id__in = option_pks).count()
        for option in question.option_set.all():
            # get the number of answers only for that option
            num_answers = Answer.objects.filter(option = option).count()
            # and compute %age -- set it to the option
            option.percent = 100.0 * num_answers / total_answers if total_answers else 0
    
    host = request.get_host()
    public_path = reverse("survey-start", args = [pk]) # get the url wrt pk
    public_url = f"{request.scheme}://{host}/{public_path}"
    
    # completed submissions
    num_submissions = survey.submission_set.filter(is_complete = True).count() 
    return render(
        request, # user info
        "survey_tmpl/detail.html", # template info
        {
            "survey": survey, # survey to be expanded in detail
            "public_url": public_url, # dunno
            "questions": questions, 
            "num_submissions": num_submissions
        },
    ) # question: why did we compute those percentages then? only to update option? and probably display a bar?

@login_required
def create(request):
    """create a new survey"""
    if request.method == "POST":
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit = False)
            survey.creator = request.user
            survey.save()
            return redirect("survey-edit", pk = survey.id) # go to next page survey-edit view [ka GET probs]
        else:
            form = SurveyForm() # give them the survey form
        
    return render(request, "survey_tmpl/create.html", {"form" : form})

@login_required
def delete(request, pk):
    """"delete a survey"""
    survey = get_object_or_404(Survey, pk = pk, creator = request.user)
    if request.method == "POST":
        survey.delete()

    return redirect("survey-list") # just show the list page

@login_required
def edit(request, pk):
    """"add ques to survey, then activate survey"""
    try:
        survey = Survey.objects.prefetch_related("question_set__option_set").get(
            pk = pk, creator = request.user, is_active = False
        )
    except Survey.DoesNotExist:
        raise Http404()

    if request.method == "POST":
        survey.is_active = True
        survey.save() # update the survey.. coz you have chosen it to edit
        # it was false till now
        return redirect("survey-detail", pk = pk)
    else:
        # didn't understand what a get request would do in this view
        questions = survey.question_set.all()
        return render(request, "survey_tmpl/edit.html", {"survey": survey, "questions": questions})

@login_required
def question_create(request, pk):
    """adds question if survey with pk exists"""
    survey = get_object_or_404(Survey, pk = pk, creator = request.user)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit = False)
            question.survey = survey # set its survey
            question.save() # now save it
            # now send to options create page
            return redirect("survey-option-create", survey_pk = pk, question_pk = question.pk)
    else:
        form = QuestionForm()
    
    return render(request, "survey_tmpl/question.html", {"survey" : survey, "form" : form})

@login_required
def option_create(request, survey_pk, question_pk):
    survey = get_object_or_404(Survey, pk = survey_pk, creator = request.user)
    question = Question.objects.get(pk = question_pk) # why not considering anything else
    # coz its fully obtainable by question_pk
    if request.method == "POST":
        form = OptionForm(request.POST)
        if form.is_valid():
            option = form.save(commit = False)
            option.question_id = question_pk
            option.save()
    else:
        form = OptionForm()

    options = question.option_set.all() 
    return render(request, "survey_tmpl/options.html", {"survey": survey, "question": question, 
    "options": options, "form": form})

def start(request, pk):
    """survey-taker can start"""
    survey = get_object_or_404(Survey, pk = pk, is_active = True)
    if request.method == "POST":
        sub = Submission.objects.create(survey = survey)
        return redirect("survey-submit", survey_pk = pk, sub_pk = sub.pk)

    return render(request, "survey_tmpl/start.html", {"survey" : survey})

def submit(request, survey_pk, sub_pk):
    try:
        survey = Survey.objects.prefetch_related("question_set__option_st").get(
            pk = survey_pk, is_active = True
        )
    except Survey.DoesNotExist:
        raise Http404()

    try:
        sub = survey.submission_set.get(pk = sub_pk, is_complete = False)
    except Submission.DoesNotExist:
        raise Http404()

    questions = survey.questions_set.all()
    options = [q.option_set.all() for q in questions] # note!!
    form_kwargs = {"empty_permitted": False, "options" : options} # option HAS to be chosen
    AnswerFormSet = formset_factory(AnswerForm, extra = len(questions), formset = BaseAnswerFormSet)

    if request.method == "POST":
        formset = AnswerFormSet(request.POST, form_kwargs = form_kwargs)
        if formset.is_valid():
            with transaction.atomic(): # what does this line mean
                for form in formset:
                    Answer.objects.create( # record all answers
                        option_id = form.cleaned_data["option"], submission_id = sub_pk,
                    )
                sub.is_complete = True # all answers recorded
                sub.save()
            return redirect("survey-thanks", pk = survey_pk)
    else:
        formset = AnswerFormSet(form_kwargs = form_kwargs)

    question_forms = zip(questions, formset)
    return render(
        request,
        "survey_tmpl/submit.html",
        {"survey": survey, "question_forms": question_forms, "formset": formset} # whats this formset thing
    )

def thanks(request, pk):
    """thanks for filling the survey, dear survey-taker"""
    survey = get_object_or_404(Survey, pk = pk, is_active = True)
    return render(request, "survey_tmpl/thanks.html", {"survey": survey})