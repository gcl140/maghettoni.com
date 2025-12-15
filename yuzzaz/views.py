from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token
from .forms import UserRegistrationForm
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.sites.shortcuts import get_current_site
from datetime import timedelta, datetime
from yuzzaz.forms import UserRegistrationForm, CustomUserForm
from django.contrib.auth.decorators import login_required
from yuzzaz.tokens import account_activation_token
import random
# from content.views import general_context
# from content.models import Joke
User = get_user_model()

def landing(request):
    context = {
        'year': datetime.now().year,
    }
    return render(request, 'yuzzaz/home.html', context)

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Send activation email
            if user.email:
                current_site = get_current_site(request)
                message = render_to_string("yuzzaz/activate_account.html", {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': 'https' if request.is_secure() else 'http',
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'current_year': datetime.now().year,
                })
                email = EmailMessage("Activate your user account", message, to=[user.email])
                email.content_subtype = "html"
                email.send()

            # Store session for resend logic
            request.session['inactive_user_email'] = user.email
            # request.session['email_sent_time'] = datetime.now().isoformat()
            request.session['email_sent_time'] = now().isoformat()


            messages.success(request, f"Mpendwa {user.first_name} {user.last_name}, tumetuma kiungo cha kuamilisha kwenye nambari yako ya simu na barua pepe yako. Tafadhali angalia meseji zako au barua pepe yako kukamilisha usajili")
            return redirect('activation_sent')
    else:
        form = UserRegistrationForm()

    return render(request, 'yuzzaz/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if not user:
        messages.error(request, "Kiungo cha uamilishaji si sahihi.")
        return redirect('home')

    if user.is_active:
        messages.info(request, "Akaunti tayari imeamilishwa. Unaweza kuingia.")
        return redirect('login')

    if not account_activation_token.check_token(user, token):
        messages.error(request, "Kiungo cha uamilishaji si sahihi au kimeisha muda.")
        return redirect('home')

    user.is_active = True
    user.save()
    messages.success(request, "Asante kwa kuthibitisha barua pepe yako. Akaunti yako sasa imeamilishwa, na unaweza kuingia sasa.")
    return redirect('login')

def activation_sent(request):
    email = request.session.get('inactive_user_email')
    if not email:
        messages.warning(request, "Hakuna ombi la uamilishaji lililopatikana.")
        return redirect('login')  # Use your standard register route

    if not request.session.get('email_sent_time'):
        request.session['email_sent_time'] = now().isoformat()

    return render(request, 'yuzzaz/activation_sent.html', {
        'email': email,
        'can_resend_at': now() + timedelta(seconds=90),
    })

def resend_activation_email(request):
    email = request.session.get('inactive_user_email')
    sent_time = request.session.get('email_sent_time')

    if not email or not sent_time:
        messages.error(request, "Kipindi kimeisha. Tafadhali jisajili tena.")
        return redirect('register')

    sent_time = datetime.fromisoformat(sent_time)

    user = User.objects.filter(email=email, is_active=False).first()
    if user:
        current_site = get_current_site(request)
        message = render_to_string("yuzzaz/activate_account.html", {
            'user': user,
            'domain': current_site.domain,
            'protocol': 'https' if request.is_secure() else 'http',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            'current_year': datetime.now().year,
        })
        email_obj = EmailMessage("Activate your user account", message, to=[user.email])
        email_obj.content_subtype = "html"
        email_obj.send()

        request.session['email_sent_time'] = now().isoformat()
        messages.success(request, "Kiungo kipya cha uamilishaji kimetumwa.")
    else:
        messages.error(request, "Hakuna akaunti isiyoamilishwa iliyopatikana na barua pepe hiyo.")

    return redirect('activation_sent')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                request.session['inactive_user_email'] = user.email
                request.session['email_sent_time'] = now().isoformat()
                messages.warning(request, "Akaunti yako haijamilishwa. Tafadhali angalia barua pepe yako au tuma tena kiungo cha uamilishaji.")
                return redirect('activation_sent')

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Umefanikiwa kuingia.")
            if user.is_staff:
                return redirect('home')
            else:
                return redirect('dashboard')  # Standard redirect — adjust to your default user landing page

        messages.error(request, "Taarifa zako si sahihi, tafadhali jaribu tena.")

    return render(request, 'yuzzaz/login.html')

def logout(request):
    auth_logout(request)
    messages.success(request, "Umetoka nje kikamilifu.")
    return redirect('login')


@login_required
def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Wasifu wako umesasishwa!")
            return redirect('profile', user_id=user.id)  # Redirect to the same page
        else:
            print(form.errors)

    else:
        form = CustomUserForm(instance=user)
    jokess = Joke.objects.filter(joke_by=user).order_by('-created_at')
    context = {
        'logged_in_user': request.user,
        'looking_at': user,
        'jokess': jokess,
        'form': form,
    }
    context.update(general_context(request))
    return render(request, 'yuzzaz/profile.html', context)


def company_profile(request):
    context = {        
    }
    return render(request, 'yuzzaz/company_profile.html', context)

def logout_and_login(request):
    auth_logout(request)
    return redirect(f"{reverse('social:begin', args=['google-oauth2'])}?next=/profile/")



@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wasifu umesasishwa kikamilifu!')
            return redirect('view_profile', id=request.user.id)
    else:
        form = CustomUserForm(instance=request.user)

    return render(request, 'yuzzaz/partials/edit_profile_modal.html', {'form': form, 'viewing_user': request.user})
    
    

def custom_404_view(request, exception):
    return render(request, 'partials/404.html', status=404)