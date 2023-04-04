from pydantic import BaseModel


class EncodingSchema(BaseModel):
    id: int


class EmployeeBase(BaseModel):
    fullname: str
    encoding_id: int
    image_id: int


class Employee(EmployeeBase):
    class Config:
        orm_mode = True
