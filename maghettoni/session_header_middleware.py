import logging
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class SessionHeaderMiddleware:
    """
    Allows API clients (Flutter, mobile) to authenticate via
    X-Session-Key header instead of a Cookie, since browsers block
    JavaScript from reading HttpOnly session cookies.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            key = request.headers.get('X-Session-Key')
            logger.debug('SessionHeaderMiddleware: key=%s path=%s', key, request.path)
            if key:
                session = SessionStore(session_key=key)
                uid = session.get('_auth_user_id')
                backend = session.get('_auth_user_backend')
                logger.debug('SessionHeaderMiddleware: uid=%s backend=%s', uid, backend)
                if uid and backend:
                    try:
                        request.user = User.objects.get(pk=uid)
                        request.session = session
                        logger.debug('SessionHeaderMiddleware: authenticated user=%s', request.user)
                    except User.DoesNotExist:
                        logger.warning('SessionHeaderMiddleware: user pk=%s not found', uid)
        return self.get_response(request)
