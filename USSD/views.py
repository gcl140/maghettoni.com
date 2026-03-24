import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .engine import USSDEngine


@csrf_exempt
@require_http_methods(["GET", "POST"])
def ussd_callback(request):
    """
    Generic USSD callback endpoint.

    Accepts form-encoded or JSON payloads from a USSD gateway.
    Expected keys (gateway-dependent aliases supported):
      - sessionId / session_id
      - serviceCode / service_code
      - phoneNumber / msisdn / phone_number
      - text / user_input
    Returns plain text with CON/END prefix.
    """
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "message": "USSD callback is alive. POST session payload to interact.",
                "expected_fields": ["sessionId", "serviceCode", "phoneNumber", "text"],
            }
        )

    payload = {}
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}

    if not payload:
        payload = request.POST.dict()

    session_id = payload.get("sessionId") or payload.get("session_id") or ""
    service_code = payload.get("serviceCode") or payload.get("service_code") or ""
    phone_number = (
        payload.get("phoneNumber")
        or payload.get("msisdn")
        or payload.get("phone_number")
        or ""
    )
    text = payload.get("text") or payload.get("user_input") or ""

    engine = USSDEngine()
    body = engine.handle(
        session_id=session_id,
        service_code=service_code,
        msisdn=phone_number,
        text=text,
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
