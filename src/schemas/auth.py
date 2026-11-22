from pydantic import BaseModel


class LoginViaTelegramRequest(BaseModel):
    id_token: str
