from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView # why tho -- coz we wanna update loginview
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect

def signup(request):
    if request.method == "POST":
        # if someone requested with data too
        form = UserCreationForm(request.POST) # process the form data
        if form.is_valid(): # if form makes sense
            form.save() # probably adds to db
            return redirect("login") # take user to login.html (rendered with view below)
            # redirect comes from shortcuts
    else:
        form = UserCreationForm() # empty form -- probably asks email id and pass
        
    # if it was a get request... just show the form and ask user to fill
    return render(request, "auth/signup.html", {"form" : form})

class LoginView(BaseLoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True 

login = LoginView.as_view()