from pydantic import BaseModel, EmailStr, field_validator, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Минимальные требования к паролю:
        - 8–128 символов
        - Хотя бы одна цифра или специальный символ
        """
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v)
        if not (has_digit or has_special):
            raise ValueError("Пароль должен содержать хотя бы одну цифру или специальный символ")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v)
        if not (has_digit or has_special):
            raise ValueError("Пароль должен содержать хотя бы одну цифру или специальный символ")
        return v