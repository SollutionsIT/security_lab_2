from __future__ import annotations

from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_LAB_HOSTS = frozenset({"127.0.0.1", "localhost", "lab-api"})


class SecurityTestSettings(BaseSettings):
    """Runtime inputs for tests; credentials and targets never live in test code."""

    model_config = SettingsConfigDict(
        env_file="tests/security/.env",
        env_file_encoding="utf-8",
        env_prefix="SECURITY_TEST_",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str
    lab_test_key: str
    webhook_secret: str
    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    ai_allowed_source_url: str
    user_a_email: str
    user_a_password: str
    user_b_email: str
    user_b_password: str
    admin_email: str
    admin_password: str
    unknown_email: str
    replacement_password: str
    request_timeout_seconds: float = 5.0

    def model_post_init(self, _context: object, /) -> None:
        parsed = urlsplit(self.base_url)
        try:
            parsed_port = parsed.port
        except ValueError as error:
            raise ValueError("SECURITY_TEST_BASE_URL contains an invalid port") from error

        if (
            parsed.scheme != "http"
            or parsed.hostname not in _ALLOWED_LAB_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
            or parsed_port is None
        ):
            raise ValueError(
                "SECURITY_TEST_BASE_URL must be an explicit http URL for "
                "127.0.0.1, localhost, or the lab-api container host, including a port"
            )
        if not 1 <= parsed_port <= 65_535:
            raise ValueError("SECURITY_TEST_BASE_URL port is outside the valid range")
        if not 0.1 <= self.request_timeout_seconds <= 30:
            raise ValueError("SECURITY_TEST_REQUEST_TIMEOUT_SECONDS must be between 0.1 and 30")
        if len(self.lab_test_key) < 16:
            raise ValueError("SECURITY_TEST_LAB_TEST_KEY must contain at least 16 characters")
        if len(self.webhook_secret.encode("utf-8")) < 24:
            raise ValueError("SECURITY_TEST_WEBHOOK_SECRET must contain at least 24 bytes")
        if len(self.jwt_secret.encode("utf-8")) < 32:
            raise ValueError("SECURITY_TEST_JWT_SECRET must contain at least 32 bytes")
        if not 3 <= len(self.jwt_issuer) <= 128:
            raise ValueError("SECURITY_TEST_JWT_ISSUER must contain between 3 and 128 characters")
        if not 3 <= len(self.jwt_audience) <= 128:
            raise ValueError("SECURITY_TEST_JWT_AUDIENCE must contain between 3 and 128 characters")
        ai_source = urlsplit(self.ai_allowed_source_url)
        if (
            ai_source.scheme != "https"
            or not ai_source.hostname
            or ai_source.username is not None
            or ai_source.password is not None
            or ai_source.fragment
        ):
            raise ValueError("SECURITY_TEST_AI_ALLOWED_SOURCE_URL must be a bounded HTTPS URL")

        email_field_names = (
            "user_a_email",
            "user_b_email",
            "admin_email",
            "unknown_email",
        )
        for field_name in email_field_names:
            value = getattr(self, field_name)
            local, separator, domain = value.partition("@")
            if (
                not local
                or separator != "@"
                or not domain
                or "@" in domain
                or any(character.isspace() for character in value)
                or len(value) > 254
            ):
                raise ValueError(f"SECURITY_TEST_{field_name.upper()} must be a bounded email")
        if len({getattr(self, name).casefold() for name in email_field_names}) != 4:
            raise ValueError("Synthetic identity email settings must be distinct")

        password_field_names = (
            "user_a_password",
            "user_b_password",
            "admin_password",
            "replacement_password",
        )
        for field_name in password_field_names:
            value = getattr(self, field_name)
            if not 12 <= len(value) <= 128:
                raise ValueError(
                    f"SECURITY_TEST_{field_name.upper()} must contain between 12 and 128 characters"
                )
        replacement = self.replacement_password
        if not (
            any(character.islower() for character in replacement)
            and any(character.isupper() for character in replacement)
            and any(character.isdigit() for character in replacement)
            and any(not character.isalnum() for character in replacement)
        ):
            raise ValueError("SECURITY_TEST_REPLACEMENT_PASSWORD must satisfy the lab policy")
        if replacement in {
            self.user_a_password,
            self.user_b_password,
            self.admin_password,
        }:
            raise ValueError("SECURITY_TEST_REPLACEMENT_PASSWORD must differ from seed passwords")

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")
