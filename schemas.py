from pydantic import BaseModel


class UserSchema(BaseModel):
    fullname: str
