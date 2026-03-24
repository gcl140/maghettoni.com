from __future__ import annotations

from datetime import timedelta
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from django.db.models import Q
from django.utils import timezone

from dashboardd.models import MaintenanceRequest, Payment, Property, Tenant
from dashboardd.services import send_maintenance_update, send_payment_reminder, send_otp
from tathmini.models import AssessmentSubmission, PhoneVerification
from tenant_portal.models import TenantNotification, TenantPaymentSubmission
from yuzzaz.models import CustomUser


def _normalize_phone(raw: str) -> str:
    value = (raw or "").strip().replace(" ", "").replace("-", "")
    value = value.lstrip("+")
    if value.startswith("0"):
        value = "255" + value[1:]
    return value


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [p for p in full_name.strip().split(" ") if p]
    if not parts:
        return "Tenant", "User"
    if len(parts) == 1:
        return parts[0], "User"
    return parts[0], " ".join(parts[1:])


def _con(message: str) -> str:
    return f"CON {message}"


def _end(message: str) -> str:
    return f"END {message}"


@dataclass
class Actor:
    role: str
    tenant: Optional[Tenant] = None
    landlord: Optional[CustomUser] = None


class USSDEngine:
    """
    Provider-agnostic USSD state machine based on text segments.

    It is intentionally string/number-driven and maps to existing project logic.
    """

    def handle(self, session_id: str, service_code: str, msisdn: str, text: str) -> str:
        _ = session_id, service_code
        segments = [s.strip() for s in (text or "").split("*") if s.strip()]
        normalized_msisdn = _normalize_phone(msisdn)
        actor = self._resolve_actor(msisdn)

        if not actor:
            return self._public_flow(normalized_msisdn, segments)

        if actor.role == "landlord":
            return self._landlord_flow(actor.landlord, segments)

        return self._tenant_flow(actor.tenant, segments)

    def _public_flow(self, msisdn: str, segments: List[str]) -> str:
        if not msisdn:
            return _end("Namba haijasomwa. Jaribu tena.")

        if not segments:
            return _con(
                "Maghettoni Public\n"
                "1. Tuma OTP\n"
                "2. Verify OTP\n"
                "3. Check verification\n"
                "4. Submit tathmini"
            )

        cmd = segments[0]
        if cmd == "1":
            return self._public_send_otp(msisdn)
        if cmd == "2":
            return self._public_verify_otp(msisdn, segments)
        if cmd == "3":
            return self._public_check_verification(msisdn)
        if cmd == "4":
            return self._public_submit_assessment(msisdn, segments)

        return _end("Chaguo si sahihi.")

    def _public_send_otp(self, msisdn: str) -> str:
        code = PhoneVerification.generate_code()
        PhoneVerification.objects.filter(phone=msisdn).delete()
        PhoneVerification.objects.create(
            phone=msisdn,
            verification_code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        sent = send_otp(msisdn, code)
        if not sent:
            return _end("OTP haikutumwa. Kuna Hitilafu, labda jaribu tena baadae.")
        return _end("OTP imetumwa. Ingiza 2*CODE kuverify.")

    def _public_verify_otp(self, msisdn: str, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Andika OTP code")

        code = segments[1]
        verification = PhoneVerification.objects.filter(phone=msisdn, verification_code=code).first()
        if not verification:
            return _end("Code si sahihi.")
        if verification.is_expired():
            return _end("Code ime-expire. Tuma mpya.")

        verification.is_verified = True
        verification.save(update_fields=["is_verified"])
        return _end("Namba ime-verify kikamilifu.")

    def _public_check_verification(self, msisdn: str) -> str:
        verification = PhoneVerification.objects.filter(phone=msisdn, is_verified=True).first()
        if not verification:
            return _end("Namba bado haijathibitishwa.")
        if verification.is_expired():
            return _end("Uthibitisho umeisha muda. Tuma OTP tena.")
        return _end("Namba imethibitishwa.")

    def _public_submit_assessment(self, msisdn: str, segments: List[str]) -> str:
        verification = PhoneVerification.objects.filter(phone=msisdn, is_verified=True).first()
        if not verification or verification.is_expired():
            return _end("Verify namba kwanza: chagua 1 kisha 2.")

        if len(segments) == 1:
            return _con("Andika jina kamili")
        if len(segments) == 2:
            return _con("Andika email")
        if len(segments) == 3:
            return _con("Current situation: 1=notebooks 2=computer_systems 3=delegated_manager")
        if len(segments) == 4:
            return _con("Goal: 1=self_manage 2=delegate_with_visibility")

        situation_map = {
            "1": "notebooks",
            "2": "computer_systems",
            "3": "delegated_manager",
        }
        goals_map = {
            "1": "self_manage",
            "2": "delegate_with_visibility",
        }

        name = segments[1][:255]
        email = segments[2][:255]
        current_situation = situation_map.get(segments[3])
        goals = goals_map.get(segments[4])
        if not current_situation or not goals:
            return _end("Chaguo la tathmini si sahihi.")

        if AssessmentSubmission.objects.filter(phone=msisdn).exists():
            return _end("Tathmini tayari ilitumwa kwa namba hii.")

        submission = AssessmentSubmission.objects.create(
            name=name,
            email=email,
            location="USSD",
            phone=msisdn,
            current_situation=current_situation,
            goals=goals,
            challenges="record_keeping",
            solution="USSD onboarding",
            submitted_at=timezone.now(),
            ip_address=None,
            verified_phone=verification,
        )
        return _end(f"Asante! Tathmini imepokelewa. Ref #{submission.id}")

    def _resolve_actor(self, msisdn: str) -> Optional[Actor]:
        normalized = _normalize_phone(msisdn)
        if not normalized:
            return None

        tenant = (
            Tenant.objects.select_related("property", "unit", "property__owner")
            .filter(phone__endswith=normalized[-9:])
            .order_by("-created_at")
            .first()
        )
        if tenant:
            return Actor(role="tenant", tenant=tenant)

        landlord = (
            CustomUser.objects.filter(
                is_landlord=True,
                telephone__isnull=False,
            )
            .filter(Q(telephone=normalized) | Q(telephone__endswith=normalized[-9:]))
            .first()
        )
        if landlord:
            return Actor(role="landlord", landlord=landlord)

        return None

    def _tenant_flow(self, tenant: Tenant, segments: List[str]) -> str:
        if not segments:
            return _con(
                "Maghettoni Tenant\n"
                "1. Muhtasari\n"
                "2. Malipo yangu\n"
                "3. Lipa kodi\n"
                "4. Ripoti hitilafu\n"
                "5. Taarifa\n"
                "6. Washa/Zima alerts"
            )

        cmd = segments[0]
        if cmd == "1":
            return self._tenant_dashboard(tenant)
        if cmd == "2":
            return self._tenant_payments(tenant)
        if cmd == "3":
            return self._tenant_pay(tenant, segments)
        if cmd == "4":
            return self._tenant_maintenance_report(tenant, segments)
        if cmd == "5":
            return self._tenant_notifications(tenant)
        if cmd == "6":
            return self._tenant_toggle_notifications(tenant)

        return _end("Chaguo si sahihi.")

    def _tenant_dashboard(self, tenant: Tenant) -> str:
        # Keep a lightweight summary for USSD screens.
        total = tenant.payments.filter(status="completed").values_list("amount", flat=True)
        total_amount = sum(total) if total else 0
        overdue = tenant.payments.filter(status__in=["pending", "failed"], due_date__lt=timezone.now().date()).count()
        rent = tenant.unit.monthly_rent if tenant.unit else 0
        return _end(
            f"{tenant.first_name} {tenant.last_name}\n"
            f"Nyumba: {tenant.property.name}\n"
            f"Kodi/mwezi: TZS {rent:,.0f}\n"
            f"Jumla uliolipa: TZS {total_amount:,.0f}\n"
            f"Overdue: {overdue}"
        )

    def _tenant_payments(self, tenant: Tenant) -> str:
        recent = tenant.payments.order_by("-payment_date")[:3]
        if not recent:
            return _end("Hakuna rekodi za malipo bado.")

        lines = ["Malipo ya mwisho:"]
        for idx, p in enumerate(recent, start=1):
            lines.append(
                f"{idx}. TZS {p.amount:,.0f} | {p.status} | {p.payment_date}"
            )
        return _end("\n".join(lines))

    def _tenant_pay(self, tenant: Tenant, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka kiasi cha kulipa (mfano 50000)")

        try:
            amount = Decimal(segments[1])
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return _end("Kiasi si sahihi.")

        if len(segments) == 2:
            return _con(
                f"Lipa TZS {amount:,.0f}?\n"
                "1. Ndiyo\n"
                "2. Hapana"
            )

        if segments[2] != "1":
            return _end("Muamala umeghairiwa.")

        submission = TenantPaymentSubmission.objects.create(
            tenant=tenant,
            amount=amount,
            payment_method="mobile_money",
            phone_number=tenant.phone,
            status="processing",
            notes="USSD payment initiation",
        )
        return _end(
            f"Ombi la malipo limetumwa. Token: {submission.payment_token}. "
            "Tafadhali malizia kwenye mobile money prompt."
        )

    def _tenant_maintenance_report(self, tenant: Tenant, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Andika tatizo kwa kifupi (mfano: bomba limepasuka)")

        title = segments[1][:120]
        if not tenant.unit:
            return _end("Huna unit iliyounganishwa. Wasiliana na landlord.")

        req = MaintenanceRequest.objects.create(
            property=tenant.property,
            unit=tenant.unit,
            tenant=tenant,
            title=title,
            description=f"USSD report: {title}",
            priority="medium",
            status="pending",
        )
        return _end(f"Hitilafu imeripotiwa. Ref #{req.id}")

    def _tenant_notifications(self, tenant: Tenant) -> str:
        items = list(tenant.tenant_notifications.order_by("-created_at")[:3])
        if not items:
            return _end("Hakuna taarifa mpya.")

        lines = ["Taarifa zako:"]
        unread_ids = []
        for idx, n in enumerate(items, start=1):
            lines.append(f"{idx}. {n.title}")
            if not n.is_read:
                unread_ids.append(n.id)
        if unread_ids:
            TenantNotification.objects.filter(id__in=unread_ids).update(is_read=True)
        return _end("\n".join(lines))

    def _tenant_toggle_notifications(self, tenant: Tenant) -> str:
        tenant.notifications_enabled = not tenant.notifications_enabled
        tenant.save(update_fields=["notifications_enabled"])
        state = "ON" if tenant.notifications_enabled else "OFF"
        return _end(f"Alerts zimewekwa {state}.")

    def _landlord_flow(self, landlord: CustomUser, segments: List[str]) -> str:
        if not segments:
            return _con(
                "Maghettoni Landlord\n"
                "1. Alerts\n"
                "2. Tafuta tenant\n"
                "3. Ongeza tenant\n"
                "4. Activate tenant\n"
                "5. Deactivate tenant\n"
                "6. Record payment\n"
                "7. Update payment status\n"
                "8. Create maintenance\n"
                "9. Update maintenance\n"
                "10. Property summary\n"
                "11. Delete property"
            )

        cmd = segments[0]
        if cmd == "1":
            return self._landlord_alerts(landlord)
        if cmd == "2":
            return self._landlord_search_tenant(landlord, segments)
        if cmd == "3":
            return self._landlord_add_tenant(landlord, segments)
        if cmd == "4":
            return self._landlord_toggle_tenant_status(landlord, segments, "active")
        if cmd == "5":
            return self._landlord_toggle_tenant_status(landlord, segments, "inactive")
        if cmd == "6":
            return self._landlord_record_payment(landlord, segments)
        if cmd == "7":
            return self._landlord_update_payment(landlord, segments)
        if cmd == "8":
            return self._landlord_create_maintenance(landlord, segments)
        if cmd == "9":
            return self._landlord_update_maintenance(landlord, segments)
        if cmd == "10":
            return self._landlord_property_summary(landlord, segments)
        if cmd == "11":
            return self._landlord_delete_property(landlord, segments)

        return _end("Chaguo si sahihi.")

    def _landlord_alerts(self, landlord: CustomUser) -> str:
        items = list(landlord.notifications_for_user.order_by("-created_at")[:3])
        if not items:
            return _end("Hakuna alerts mpya.")
        lines = ["Alerts:"]
        unread_ids = []
        for idx, n in enumerate(items, start=1):
            lines.append(f"{idx}. {n.title}")
            if not n.is_read:
                unread_ids.append(n.id)
        if unread_ids:
            landlord.notifications_for_user.filter(id__in=unread_ids).update(is_read=True)
        return _end("\n".join(lines))

    def _landlord_search_tenant(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Andika jina/phone ya tenant")

        q = segments[1]
        tenants = Tenant.objects.filter(property__owner=landlord).filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
        )[:5]
        if not tenants:
            return _end("Hakuna tenant aliyepatikana.")

        lines = ["Matokeo:"]
        for idx, t in enumerate(tenants, start=1):
            lines.append(f"{idx}. {t.first_name} {t.last_name} ({t.id})")
        return _end("\n".join(lines))

    def _landlord_add_tenant(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            properties = Property.objects.filter(owner=landlord)[:5]
            if not properties:
                return _end("Huna properties za kuongeza tenant.")
            lines = ["Chagua Property ID:"]
            for p in properties:
                lines.append(f"{p.id}. {p.name}")
            return _con("\n".join(lines))

        if len(segments) == 2:
            return _con("Andika full name ya tenant")
        if len(segments) == 3:
            return _con("Andika phone ya tenant (2557...)")

        try:
            property_id = int(segments[1])
        except ValueError:
            return _end("Property ID si sahihi.")

        property_obj = Property.objects.filter(owner=landlord, id=property_id).first()
        if not property_obj:
            return _end("Property haijapatikana.")

        full_name = segments[2]
        phone = _normalize_phone(segments[3])
        first_name, last_name = _split_name(full_name)

        tenant = Tenant.objects.create(
            property=property_obj,
            first_name=first_name,
            last_name=last_name,
            email=f"{phone}@ussd.local",
            phone=phone,
            move_in_date=timezone.now().date(),
            status="pending",
        )
        return _end(f"Tenant ameongezwa: {tenant.first_name} {tenant.last_name} (ID {tenant.id})")

    def _landlord_toggle_tenant_status(self, landlord: CustomUser, segments: List[str], status: str) -> str:
        if len(segments) == 1:
            return _con("Weka Tenant ID")

        try:
            tenant_id = int(segments[1])
        except ValueError:
            return _end("Tenant ID si sahihi.")

        tenant = Tenant.objects.filter(property__owner=landlord, id=tenant_id).first()
        if not tenant:
            return _end("Tenant hapatikani.")

        tenant.status = status
        tenant.save(update_fields=["status"])
        return _end(f"Tenant {tenant.id} status: {status}")

    def _landlord_record_payment(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka Tenant ID")
        if len(segments) == 2:
            return _con("Weka kiasi (mfano 100000)")

        try:
            tenant_id = int(segments[1])
            amount = Decimal(segments[2])
            if amount <= 0:
                raise InvalidOperation
        except (ValueError, InvalidOperation):
            return _end("Data si sahihi.")

        tenant = Tenant.objects.filter(property__owner=landlord, id=tenant_id).first()
        if not tenant:
            return _end("Tenant hapatikani.")

        payment = Payment.objects.create(
            tenant=tenant,
            property=tenant.property,
            amount=amount,
            payment_date=timezone.now().date(),
            due_date=timezone.now().date(),
            payment_method="mobile_money",
            status="completed",
            reference_number=f"USSD-{timezone.now().strftime('%H%M%S')}-{tenant.id}",
            notes="Recorded via USSD",
            landlord_confirmed=True,
        )
        return _end(f"Payment imerekodiwa. Payment ID: {payment.id}")

    def _landlord_update_payment(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka Payment ID")
        if len(segments) == 2:
            return _con("Chagua status: 1=pending 2=completed 3=failed 4=refunded")

        status_map = {"1": "pending", "2": "completed", "3": "failed", "4": "refunded"}
        status = status_map.get(segments[2])
        if not status:
            return _end("Status si sahihi.")

        try:
            payment_id = int(segments[1])
        except ValueError:
            return _end("Payment ID si sahihi.")

        payment = Payment.objects.filter(property__owner=landlord, id=payment_id).first()
        if not payment:
            return _end("Payment haijapatikana.")

        payment.status = status
        if status == "completed":
            payment.landlord_confirmed = True
        payment.save(update_fields=["status", "landlord_confirmed"])

        if status in {"pending", "failed"}:
            send_payment_reminder(payment.tenant, payment)

        return _end(f"Payment {payment.id} imebadilishwa kuwa {status}")

    def _landlord_create_maintenance(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka Tenant ID")
        if len(segments) == 2:
            return _con("Andika title ya issue")

        try:
            tenant_id = int(segments[1])
        except ValueError:
            return _end("Tenant ID si sahihi.")

        tenant = Tenant.objects.filter(property__owner=landlord, id=tenant_id).first()
        if not tenant or not tenant.unit:
            return _end("Tenant au unit haijapatikana.")

        title = segments[2][:120]
        req = MaintenanceRequest.objects.create(
            property=tenant.property,
            unit=tenant.unit,
            tenant=tenant,
            title=title,
            description=f"USSD landlord issue: {title}",
            priority="medium",
            status="pending",
        )
        return _end(f"Maintenance ticket imeundwa. Ref #{req.id}")

    def _landlord_update_maintenance(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka Request ID")
        if len(segments) == 2:
            return _con("Status mpya: 1=pending 2=in_progress 3=completed 4=cancelled")

        status_map = {
            "1": "pending",
            "2": "in_progress",
            "3": "completed",
            "4": "cancelled",
        }
        status = status_map.get(segments[2])
        if not status:
            return _end("Status si sahihi.")

        try:
            request_id = int(segments[1])
        except ValueError:
            return _end("Request ID si sahihi.")

        req = MaintenanceRequest.objects.filter(property__owner=landlord, id=request_id).first()
        if not req:
            return _end("Request haijapatikana.")

        req.status = status
        if status == "completed" and not req.completed_date:
            req.completed_date = timezone.now()
        req.save(update_fields=["status", "completed_date"])
        send_maintenance_update(req.tenant, req)
        return _end(f"Request {req.id} status: {status}")

    def _landlord_property_summary(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            props = Property.objects.filter(owner=landlord)[:5]
            if not props:
                return _end("Hakuna property.")
            lines = ["Chagua Property ID:"]
            for p in props:
                lines.append(f"{p.id}. {p.name}")
            return _con("\n".join(lines))

        try:
            property_id = int(segments[1])
        except ValueError:
            return _end("Property ID si sahihi.")

        p = Property.objects.filter(owner=landlord, id=property_id).first()
        if not p:
            return _end("Property haijapatikana.")

        units = p.units_list.count()
        occupied = p.units_list.filter(is_occupied=True).count()
        tenants = p.tenants.count()
        return _end(
            f"{p.name}\nUnits: {units}\nOccupied: {occupied}\nTenants: {tenants}"
        )

    def _landlord_delete_property(self, landlord: CustomUser, segments: List[str]) -> str:
        if len(segments) == 1:
            return _con("Weka Property ID")
        if len(segments) == 2:
            return _con("Thibitisha kufuta: andika YES")

        if segments[2].upper() != "YES":
            return _end("Uthibitisho umeshindwa. Haijafutwa.")

        try:
            property_id = int(segments[1])
        except ValueError:
            return _end("Property ID si sahihi.")

        p = Property.objects.filter(owner=landlord, id=property_id).first()
        if not p:
            return _end("Property haijapatikana.")

        if p.units_list.filter(is_occupied=True).exists():
            return _end("Haiwezi kufutwa: kuna units occupied.")

        name = p.name
        p.delete()
        return _end(f"Property '{name}' imefutwa.")
