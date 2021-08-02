from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


def register(request):

    if request.method == "POST":
        usercreation_form = UserCreationForm(request.POST)
        if usercreation_form.is_valid():
            # create the user
            new_user = usercreation_form.save()
            # now automatically sign them in
            new_user = authenticate(
                username=usercreation_form.cleaned_data["username"],
                password=usercreation_form.cleaned_data["password1"],
            )
            login(request, new_user)
            # after first creating a profile, I send them to their profile page
            return redirect("profile")
    else:
        usercreation_form = UserCreationForm()

    context = {
        "usercreation_form": usercreation_form,
        "active_tab_id": "profile",
    }
    template = "registration/register.html"
    return render(request, template, context)


@login_required
def profile(request):
    # !!! For future reference, you can grab user-associated data via...
    # data = request.user.relateddata.all()

    context = {"active_tab_id": "profile"}
    template = "registration/profile.html"
    return render(request, template, context)


def loginstatus(request):
    context = {"active_tab_id": "profile"}  # we just want the premade template
    template = "registration/loginstatus.html"
    return render(request, template, context)


"""
The following views are mapped automatically, so for reference I write out
the template names below. To see the source code, visit
https://github.com/django/django/blob/master/django/contrib/auth/views.py

    accounts/login/ [name='login']
        template = 'registration/login.html' by default
        on successful login, redirects to settings.LOGIN_REDIRECT_URL

    accounts/logout/ [name='logout']
        template = 'registration/logged_out.html' by default
        on successful logout, redirects to settings.LOGOUT_REDIRECT_URL



    # TODO: the below views are not fully setup yet

    accounts/password_change/ [name='password_change']
        template_name = 'registration/password_change_form.html'

    accounts/password_change/done/ [name='password_change_done']
        template_name = 'registration/password_change_done.html'

    accounts/password_reset/ [name='password_reset']
        email_template = 'registration/password_reset_email.html'
        subject_template = 'registration/password_reset_subject.txt'
        template = 'registration/password_reset_form.html'

    accounts/password_reset/done/ [name='password_reset_done']
        template = 'registration/password_reset_done.html'

    accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
        template = 'registration/password_reset_confirm.html'

    accounts/reset/done/ [name='password_reset_complete']
        template_name = 'registration/password_reset_complete.html'
"""
