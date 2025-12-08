
# edupay/pipeline.py
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from social_django.models import UserSocialAuth


from yuzzaz.models import CustomUser
User = get_user_model()

def save_user_details(backend, user, response, request=None, *args, **kwargs):
    if backend.name != 'google-oauth2':
        return

    google_email = response.get("email")
    if request and user and user.email and user.email != google_email:
        messages.error(request, "You're logged in as a different user. Please log out first before using this Google account.")
        logout(request)
        return

    is_new = kwargs.get('is_new', False)

    if is_new or not user.first_name:
        user.first_name = response.get('given_name', user.first_name)

    if is_new or not user.last_name:
        user.last_name = response.get('family_name', user.last_name)

    if is_new:
        user.is_active = True
        user.username = user.email  # safe assumption here
    user.save()
    messages.success(request, "Successfully logged in with Google.")



def prevent_duplicate_social_auth(strategy, backend, uid, user=None, *args, **kwargs):
    request = strategy.request
    User = get_user_model()

    existing_social = UserSocialAuth.objects.filter(provider=backend.name, uid=uid).first()

    if existing_social:
        if user and existing_social.user != user:
            messages.error(request, "This Google account is already linked to another user. You were logged out for security reasons. Please login again")
            logout(request)
            return {'user': None}
        elif not user:
            return {'user': existing_social.user}

    email = kwargs.get('details', {}).get('email')
    if email:
        existing_user = User.objects.filter(email=email).first()
        already_linked = UserSocialAuth.objects.filter(user=existing_user, provider=backend.name).exists() if existing_user else False

        if existing_user and not already_linked:
            messages.error(request, "An account with this email already exists but is not linked to Google. Please login normally and link your account from your profile settings.")
            return redirect('login')  
    return {}

