from django.shortcuts import redirect

ALLOWED_PATHS = [
    '/home/pending-approval/',
    '/home/logout/',
    '/home/api/logout/',
    '/static/',
    '/media/',
]


class ApprovalGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not getattr(request.user, 'is_verified', True)
            and not request.user.is_staff
            and not request.user.is_superuser
        ):
            if not any(request.path.startswith(p) for p in ALLOWED_PATHS):
                return redirect('pending_approval')
        return self.get_response(request)
