import string
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_email_service
from app.core.config import settings
from app.database import SessionLocal
from app.main import app
from app.models.otp import OTP, OTPType
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.jwt_service import JWTService, JWTServiceError


class DummyEmailService:
    def __init__(self):
        self.sent_otps = []

    async def send_verification_otp(self, email: str, otp_code: str) -> None:
        self.sent_otps.append((email, otp_code))


class FailingEmailService:
    async def send_verification_otp(self, email: str, otp_code: str) -> None:
        raise RuntimeError("SMTP rejected credentials")


def register_verify_and_login(client: TestClient, email: str, password: str):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Codex Auth Test",
            "email": email,
            "password": password
        }
    )
    assert register_response.status_code == 201
    user_id = UUID(register_response.json()["user_id"])

    db = SessionLocal()
    try:
        otp = (
            db.query(OTP)
            .filter(
                OTP.user_id == user_id,
                OTP.otp_type == OTPType.EMAIL_VERIFICATION
            )
            .order_by(OTP.created_at.desc())
            .first()
        )
        assert otp is not None
        otp_code = otp.otp_code
    finally:
        db.close()

    verify_response = client.post(
        "/auth/verify-email",
        json={"email": email, "otp_code": otp_code}
    )
    assert verify_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    return login_response.json()


def test_register_requires_email_otp_before_login():
    email_service = DummyEmailService()
    app.dependency_overrides[get_email_service] = lambda: email_service
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = False
    client = TestClient(app)
    email = f"codex.auth.{uuid4()}@example.com"
    password = "TestPass123"

    try:
        register_response = client.post(
            "/auth/register",
            json={
                "name": "Codex Auth Test",
                "email": email,
                "password": password
            }
        )
        assert register_response.status_code == 201
        user_id = UUID(register_response.json()["user_id"])

        login_before_verify = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert login_before_verify.status_code == 403
        assert email_service.sent_otps

        db = SessionLocal()
        try:
            otp = (
                db.query(OTP)
                .filter(
                    OTP.user_id == user_id,
                    OTP.otp_type == OTPType.EMAIL_VERIFICATION
                )
                .order_by(OTP.created_at.desc())
                .first()
            )
            assert otp is not None
            otp_code = otp.otp_code
        finally:
            db.close()

        verify_response = client.post(
            "/auth/verify-email",
            json={"email": email, "otp_code": otp_code}
        )
        assert verify_response.status_code == 200

        login_after_verify = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert login_after_verify.status_code == 200
        assert login_after_verify.json()["access_token"]
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_register_returns_503_when_verification_email_cannot_be_sent():
    app.dependency_overrides[get_email_service] = lambda: FailingEmailService()
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = False
    client = TestClient(app)
    email = f"codex.smtp-fail.{uuid4()}@example.com"

    try:
        response = client.post(
            "/auth/register",
            json={
                "name": "Codex SMTP Failure Test",
                "email": email,
                "password": "TestPass123"
            }
        )

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert "could not be sent" in detail["message"]

        db = SessionLocal()
        try:
            assert db.query(User).filter(User.email == email).first() is None
        finally:
            db.close()
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_register_returns_debug_otp_when_enabled_and_email_fails():
    app.dependency_overrides[get_email_service] = lambda: FailingEmailService()
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = True
    client = TestClient(app)
    email = f"codex.debug-otp.{uuid4()}@example.com"

    try:
        response = client.post(
            "/auth/register",
            json={
                "name": "Codex Debug OTP Test",
                "email": email,
                "password": "TestPass123"
            }
        )

        assert response.status_code == 201
        body = response.json()
        debug_otp = body["debug_otp"]
        assert len(debug_otp) == 8
        assert any(char in string.ascii_lowercase for char in debug_otp)
        assert any(char in string.ascii_uppercase for char in debug_otp)
        assert any(char in string.digits for char in debug_otp)
        assert any(char in "!@#$%^&*" for char in debug_otp)

        verify_response = client.post(
            "/auth/verify-email",
            json={"email": email, "otp_code": debug_otp}
        )
        assert verify_response.status_code == 200
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_register_allows_short_name_and_short_password():
    app.dependency_overrides[get_email_service] = lambda: FailingEmailService()
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = True
    client = TestClient(app)
    email = f"codex.short-credentials.{uuid4()}@example.com"
    password = "x"

    try:
        register_response = client.post(
            "/auth/register",
            json={
                "name": "A",
                "email": email,
                "password": password
            }
        )
        assert register_response.status_code == 201
        debug_otp = register_response.json()["debug_otp"]

        verify_response = client.post(
            "/auth/verify-email",
            json={"email": email, "otp_code": debug_otp}
        )
        assert verify_response.status_code == 200

        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["name"] == "A"
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_resend_verification_otp_sends_new_otp_for_unverified_user():
    email_service = DummyEmailService()
    app.dependency_overrides[get_email_service] = lambda: email_service
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = False
    client = TestClient(app)
    email = f"codex.resend.{uuid4()}@example.com"

    try:
        register_response = client.post(
            "/auth/register",
            json={
                "name": "Codex Resend Test",
                "email": email,
                "password": "TestPass123"
            }
        )
        assert register_response.status_code == 201

        resend_response = client.post(
            "/auth/resend-verification-otp",
            json={"email": email}
        )

        assert resend_response.status_code == 200
        assert resend_response.json()["message"] == "Verification OTP sent successfully."
        assert len(email_service.sent_otps) == 2
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_refresh_token_creates_new_access_token():
    email_service = DummyEmailService()
    app.dependency_overrides[get_email_service] = lambda: email_service
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = False
    client = TestClient(app)
    email = f"codex.refresh.{uuid4()}@example.com"
    password = "TestPass123"

    try:
        login_body = register_verify_and_login(client, email, password)
        old_access_token = login_body["access_token"]
        refresh_token = login_body["refresh_token"]

        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token != old_access_token
        assert refresh_response.json()["token_type"] == "bearer"
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_logout_revokes_refresh_token_and_blocks_refresh():
    email_service = DummyEmailService()
    app.dependency_overrides[get_email_service] = lambda: email_service
    previous_debug_setting = settings.AUTH_DEBUG_OTP_IN_RESPONSE
    settings.AUTH_DEBUG_OTP_IN_RESPONSE = False
    client = TestClient(app)
    email = f"codex.logout.{uuid4()}@example.com"
    password = "TestPass123"

    try:
        login_body = register_verify_and_login(client, email, password)
        refresh_token = login_body["refresh_token"]

        logout_response = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token}
        )
        assert logout_response.status_code == 200

        db = SessionLocal()
        try:
            token_record = (
                db.query(RefreshToken)
                .filter(RefreshToken.token == refresh_token)
                .first()
            )
            assert token_record is not None
            assert token_record.is_revoked is True
        finally:
            db.close()

        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 401
    finally:
        settings.AUTH_DEBUG_OTP_IN_RESPONSE = previous_debug_setting
        app.dependency_overrides.clear()


def test_access_token_expires_from_exp_claim():
    jwt_service = JWTService(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=-1,
        refresh_token_expire_days=7
    )
    expired_token = jwt_service.create_access_token(uuid4())

    try:
        jwt_service.verify_access_token(expired_token)
    except JWTServiceError as exc:
        assert "Invalid token" in str(exc)
    else:
        raise AssertionError("Expired access token should not verify")
