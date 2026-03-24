# Maghettoni URL Endpoint Map

Generated from URL configs and view logic across:
- maghettoni/urls.py
- yuzzaz/urls.py
- tathmini/urls.py
- dashboardd/urls.py
- tenant_portal/urls.py

Notes:
- Methods are inferred from decorators and view code.
- Access column reflects auth/decorator checks in view logic.
- JSON API endpoints are mostly under /api or /api/v1 prefixes.

## 1) Project-Level Routes (maghettoni)

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /sw.js | GET | Public | service_worker | Serves PWA service worker JS from static files with Service-Worker-Allowed header. |
| /manifest.json | GET | Public | pwa_manifest | Serves PWA manifest from static files. |
| / | GET | Public | yuzzaz.views.landing | Landing page. |
| /admin/ | GET/POST | Admin | django admin site | Django admin panel. |
| /home/ | Mixed | Public/Auth | include(yuzzaz.urls) | Mounts all auth and profile routes below. |
| /tathmini/ | Mixed | Public/Auth | include(tathmini.urls) | Mounts onboarding/assessment endpoints below. |
| /dashboard/ | Mixed | Landlord auth | include(dashboardd.urls) | Mounts landlord dashboard + APIs below. |
| /tenant/ | Mixed | Tenant auth/public invite | include(tenant_portal.urls) | Mounts tenant portal + APIs below. |
| /accounts/login/ | GET | Public | RedirectView | Permanent redirect to /login/. |
| /oauth/login/google/ | GET | Public | logout_then_google | Logs user out then redirects to Google OAuth login flow. |
| /oauth/ | Mixed | Public/Auth | include(social_django.urls) | Social auth endpoints namespace (begin/complete/disconnect). |

## 2) yuzzaz App Routes (prefix: /home/)

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /home/ | GET | Public | landing | Renders home page. |
| /home/register/ | GET | Public | register | Registration closed page (invite/admin onboarding only). |
| /home/activate/<uidb64>/<token>/ | GET | Public | activate | Activates account from email token if valid. |
| /home/login/ | GET/POST | Public | login | Username/email/phone login; checks active and verified flags; routes tenant vs landlord dashboard. |
| /home/logout/ | GET | Authenticated | logout | Ends session and redirects to login. |
| /home/profile/<int:user_id>/ | GET/POST | Login required | profile | View/update profile; supports password change when viewing own profile. |
| /home/login/google/ | GET | Public | logout_and_login | Clears session and starts Google OAuth flow. |
| /home/password_reset/ | GET/POST | Public | PasswordResetView | Built-in password reset request page/email trigger. |
| /home/password_reset_done/ | GET | Public | PasswordResetDoneView | Built-in password reset sent confirmation page. |
| /home/reset/<uidb64>/<token>/ | GET/POST | Public | PasswordResetConfirmView | Built-in password reset confirm form. |
| /home/reset_done/ | GET | Public | PasswordResetCompleteView | Built-in password reset completion page. |
| /home/activation-sent/ | GET | Public | activation_sent | Shows activation-sent status and resend timing. |
| /home/resend-activation/ | GET/POST | Public | resend_activation_email | Resends account activation email for inactive account stored in session. |
| /home/profile/edit/ | GET/POST | Login required | edit_profile | Updates logged-in user profile from modal/edit form. |
| /home/company-profile/ | GET | Public | company_profile | Company profile static page. |
| /home/set-language/ | POST | Login required | set_language_preference | Stores user preferred language (en/sw). |
| /home/send-gift-text/ | GET/POST | Public | send_gift_a_text | Accepts assessment/contact payload; requires OTP session flag for phone; sends email. |
| /home/send-lissa-text/ | GET/POST | Public | send_lissa_text | Sends contact message email without OTP gate. |
| /home/otp/send/ | POST | Public | otp_send | Generates and sends OTP to phone via SMS provider; stores OTP record. |
| /home/otp/verify/ | POST | Public | otp_verify | Verifies OTP code and stamps session otp_verified_<phone>. |
| /home/api/login/ | POST | Public | flutter_views.api_login | JSON login endpoint for mobile; returns role and session key. |

## 3) tathmini App Routes (prefix: /tathmini/)

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /tathmini/api/send-verification/ | POST | Public | send_verification_code | Sends phone verification code via SMS, stores expiry (10 min). |
| /tathmini/api/verify-phone/ | POST | Public | verify_phone_code | Verifies submitted phone code and marks verification record. |
| /tathmini/api/check-verification/ | GET | Public | check_phone_verified | Checks if a phone is verified and still valid. |
| /tathmini/api/submit-assessment/ | POST | Public | submit_assessment | Validates payload + phone verification, stores assessment submission. |
| /tathmini/admin/assessment-dashboard/ | GET | Login required | assessment_dashboard | Shows submissions analytics dashboard (counts/groupings). |
| /tathmini/subscribe/ | POST (plus fallback) | Public | subscribe | Newsletter subscription endpoint with email validation. |

## 4) dashboardd App Routes (prefix: /dashboard/)

### 4.1 Core pages, property, tenant, payment, maintenance

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /dashboard/ | GET | Landlord required | dashboard | Landlord KPI dashboard (revenue, occupancy, trends, alerts). |
| /dashboard/about/ | GET | Public | about | About/tech stack page. |
| /dashboard/properties/ | GET | Landlord required | property_list | Property listing with search, pagination, occupancy stats. |
| /dashboard/properties/add/ | GET/POST | Landlord required | property_edit | Create property with optional map/address metadata and images. |
| /dashboard/properties/edit/<int:property_id>/ | GET/POST | Landlord required | property_edit | Edit existing property. |
| /dashboard/properties/<int:property_id>/ | GET/POST | Landlord required | property_detail | Property detail; document uploads/versioning; related stats. |
| /dashboard/properties/<int:property_id>/documents/<int:document_id>/delete/ | POST | Landlord required | property_document_delete | Deletes a property document. |
| /dashboard/properties/delete/<int:property_id>/ | GET/POST | Landlord required | property_delete | Deletes property if no occupied units exist. |
| /dashboard/properties/images/<int:image_id>/delete/ | POST | Landlord required | delete_property_image | Deletes one property image. |
| /dashboard/properties/units/<int:property_id>/ | GET | Landlord required | property_units | Property units listing and unit-level metrics. |
| /dashboard/properties/<int:property_id>/units/ | GET | Landlord required | property_units | Alias route for same units listing. |
| /dashboard/properties/<int:property_id>/units/export/csv/ | GET | Landlord required | units_export_csv | Exports units for property to CSV. |
| /dashboard/properties/<int:property_id>/units/export/pdf/ | GET | Landlord required | units_export_pdf | Exports units for property to PDF. |
| /dashboard/properties/<int:property_id>/units/vacancy-alert/ | GET | Landlord required | units_vacancy_alert | Creates in-app notification summarizing current vacant units. |
| /dashboard/properties/<int:property_id>/units/add/ | GET/POST | Landlord required | unit_edit | Create a unit under a property. |
| /dashboard/properties/<int:property_id>/units/<int:unit_id>/edit/ | GET/POST | Landlord required | unit_edit | Edit existing unit under property. |
| /dashboard/properties/<int:property_id>/units/<int:unit_id>/delete/ | POST | Landlord required | unit_delete | Deletes unit and redirects to units list. |
| /dashboard/api/location/ | POST | Landlord required | location_api | Reverse geocodes lat/lng via Google Maps API key. |
| /dashboard/tenants/export/csv/ | GET | Landlord required | tenants_export_csv | Exports tenants to CSV. |
| /dashboard/tenants/export/pdf/ | GET | Landlord required | tenants_export_pdf | Exports tenants to PDF. |
| /dashboard/tenants/ | GET | Landlord required | tenant_list | Tenant list with search, pagination, status stats. |
| /dashboard/tenants/add/ | GET/POST | Landlord required | tenant_edit | Adds tenant, sets unit occupancy, sends invite email/SMS. |
| /dashboard/tenants/<int:tenant_id>/ | GET | Landlord required | tenant_detail | Tenant profile summary, payments, maintenance, eligibility. |
| /dashboard/tenants/edit/<int:tenant_id>/ | GET/POST | Landlord required | tenant_edit | Edits tenant, with lock behavior for verified tenant accounts. |
| /dashboard/api/properties/<int:property_id>/units/available/ | GET | Landlord required | get_available_units | Returns JSON list of units for selected property. |
| /dashboard/tenants/<int:tenant_id>/activate/ | GET/POST | Landlord required | tenant_activate | Marks tenant active and pushes notification. |
| /dashboard/tenants/<int:tenant_id>/deactivate/ | GET/POST | Landlord required | tenant_deactivate | Marks tenant inactive and pushes notification. |
| /dashboard/tenants/<int:tenant_id>/delete/ | GET/POST | Landlord required | tenant_delete | Deletes tenant record. |
| /dashboard/tenants/<int:tenant_id>/resend-invite/ | GET/POST | Landlord required | tenant_resend_invite | Re-sends tenant portal invite if not verified. |
| /dashboard/tenants/<int:tenant_id>/lease/ | GET | Landlord required | tenant_lease_print | Prints lease-style page with language option and eligibility info. |
| /dashboard/payments/export/csv/ | GET | Landlord required | payments_export_csv | Exports payments to CSV. |
| /dashboard/payments/export/pdf/ | GET | Landlord required | payments_export_pdf | Exports payments to PDF. |
| /dashboard/payments/ | GET | Landlord required | payments_list | Payment listing with filters and summary metrics. |
| /dashboard/payments/create/ | GET/POST | Landlord required | payment_edit | Creates payment record. |
| /dashboard/payments/<int:payment_id>/receipt/ | GET | Landlord required | payment_receipt_pdf | Generates printable PDF receipt for payment. |
| /dashboard/payments/<int:payment_id>/edit/ | GET/POST | Landlord required | payment_edit | Edits payment record. |
| /dashboard/payments/<int:payment_id>/ | GET/POST | Landlord required | payment_detail | Payment details; status update or mark paid actions. |
| /dashboard/api/tenants/<int:tenant_id>/details/ | GET | Landlord required | get_tenant_details | JSON payload of tenant + current unit info. |
| /dashboard/maintenance/export/csv/ | GET | Landlord required | maintenance_export_csv | Exports maintenance requests CSV. |
| /dashboard/maintenance/export/pdf/ | GET | Landlord required | maintenance_export_pdf | Exports maintenance requests PDF. |
| /dashboard/maintenance/ | GET | Landlord required | maintenance_requests_list | Maintenance listing with search and filters. |
| /dashboard/maintenance/create/ | GET/POST | Landlord required | maintenance_request_edit | Creates maintenance request. |
| /dashboard/maintenance/<int:request_id>/edit/ | GET/POST | Landlord required | maintenance_request_edit | Edits maintenance request. |
| /dashboard/maintenance/<int:request_id>/ | GET/POST | Landlord required | maintenance_request_detail | Detail/status update endpoint for one request. |
| /dashboard/api/properties/<int:property_id>/units-tenants/ | GET | Landlord required | get_property_units_tenants | JSON for units and tenants in a property. |
| /dashboard/search/ | GET | Landlord required | search_results | Global search across property/tenant/payment/maintenance/unit. |
| /dashboard/search/quick/ | GET | Landlord required | quick_search | Lightweight quick-search suggestion JSON. |
| /dashboard/test-sms/ | GET | Landlord required (DEBUG only) | test_sms | Dev-only Beem SMS test endpoint. |

### 4.2 Landlord JSON API routes (Flutter + web JS)

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /dashboard/api/v1/properties/ | GET | Login required | flutter_views.api_properties | Paginated list of landlord properties with filters. |
| /dashboard/api/v1/properties/<int:property_id>/ | GET | Login required | flutter_views.api_property_detail | Property detail + embedded units. |
| /dashboard/api/v1/tenants/ | GET | Login required | flutter_views.api_tenants | Paginated tenant list with search and filters. |
| /dashboard/api/v1/tenants/<int:tenant_id>/ | GET | Login required | flutter_views.api_tenant_detail | Tenant detail JSON (full variant). |
| /dashboard/api/v1/payments/ | GET | Login required | flutter_views.api_payments | Paginated payment list with filters. |
| /dashboard/api/v1/payments/<int:payment_id>/ | GET | Login required | flutter_views.api_payment_detail | Payment detail JSON. |
| /dashboard/api/v1/maintenance/ | GET | Login required | flutter_views.api_maintenance | Paginated maintenance list with filters. |
| /dashboard/api/v1/maintenance/<int:request_id>/ | GET | Login required | flutter_views.api_maintenance_detail | Maintenance request detail JSON. |
| /dashboard/api/v1/notifications/ | GET | Login required | flutter_views.api_notifications | Returns alert + in-app notifications feed, marks sliced DB items as read. |
| /dashboard/api/v1/calendar/ | GET | Login required | flutter_views.api_landlord_calendar | Calendar-style payment due/completed/overdue aggregates by day. |
| /dashboard/api/v1/payments/<int:payment_id>/remind/ | POST | Login required | flutter_views.api_payment_remind | Sends payment reminder via sms/email/both. |
| /dashboard/api/v1/maintenance/<int:request_id>/notify/ | POST | Login required | flutter_views.api_maintenance_notify | Sends maintenance update notification to tenant. |

## 5) tenant_portal App Routes (prefix: /tenant/)

### 5.1 Tenant web views

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /tenant/ | GET | Tenant required | tenant_dashboard | Tenant dashboard with rent due timeline, eligibility, stats. |
| /tenant/payments/ | GET | Tenant required | tenant_payments | Lists tenant payments and recent submissions. |
| /tenant/payments/pay/ | GET/POST | Tenant required | tenant_payment_initiate | Starts payment submission workflow. |
| /tenant/payments/process/<uuid:token>/ | GET/POST | Tenant required | tenant_payment_process | Confirms and creates Payment from submission token. |
| /tenant/payments/status/<uuid:token>/ | GET | Tenant required | tenant_payment_status | Shows status of a payment submission. |
| /tenant/maintenance/ | GET | Tenant required | tenant_maintenance | Lists tenant maintenance requests. |
| /tenant/maintenance/report/ | GET/POST | Tenant required | tenant_maintenance_create | Creates new maintenance request and landlord notification. |
| /tenant/maintenance/<int:request_id>/ | GET | Tenant required | tenant_maintenance_detail | Detail page for tenant-owned maintenance request. |
| /tenant/profile/ | GET/POST | Tenant required | tenant_profile | Tenant profile and password update, multi-tenancy context. |
| /tenant/profile/edit/ | GET/POST | Tenant required | tenant_edit_profile | Tenant profile edit page. |
| /tenant/tenancy/<int:tenancy_id>/notifications/toggle/ | POST | Tenant required | toggle_tenancy_notifications | Toggles notifications_enabled flag for a tenancy. |
| /tenant/notifications/ | GET | Tenant required | tenant_notifications | Lists and marks tenant notifications as read. |
| /tenant/invite/<uuid:token>/ | GET/POST | Public | invite_accept | Public invite acceptance flow to create tenant user account and login. |

### 5.2 Tenant JSON API routes (Flutter + web JS)

| Full Path | Method | Access | Handler | What It Does |
|---|---|---|---|---|
| /tenant/api/dashboard/ | GET | Auth + tenant profile | flutter_views.api_tenant_dashboard | Returns tenant dashboard summary JSON. |
| /tenant/api/calendar/ | GET | Auth + tenant profile | flutter_views.api_tenant_calendar | Returns tenant monthly payment calendar JSON. |
| /tenant/api/notifications/ | GET | Auth + tenant profile | flutter_views.api_tenant_notifications | Returns tenant notifications and marks unread as read. |
| /tenant/api/payments/ | GET | Auth + tenant profile | flutter_views.api_tenant_payments | Returns tenant payment history JSON. |

## 6) Quick Security/Operational Notes

- Some endpoints are csrf_exempt JSON endpoints (OTP/login/reminder flows). Keep strict rate limits and request validation at reverse proxy/app layer.
- /dashboard/test-sms/ is marked dev-only in comments and guarded by DEBUG in code; remove or hard-disable in production.
- OAuth endpoints under /oauth/ are provided by social_django include and are not fully enumerated in this file.

## 7) Defined In Code But Not Wired In URLConf

- tathmini/flutter_views.py defines mobile API equivalents for OTP/assessment, but tathmini/urls.py currently routes to tathmini/views.py.
- yuzzaz/views.py includes an api_login JSON view, but yuzzaz/urls.py points /home/api/login/ to yuzzaz/flutter_views.api_login.
