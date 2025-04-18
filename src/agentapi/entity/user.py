from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    password: str
    captcha_id: int
    captcha_code: str

class UserLogin(BaseModel):
    username: str
    password: str
    captcha_id: int
    captcha_code: str