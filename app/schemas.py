from pydantic import BaseModel
from datetime import date
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    genre: str

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    full_name: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class BorrowedBookBase(BaseModel):
    book_id: int
    user_id: int
    due_date: date
    returned_date: Optional[date] = None

class BorrowedBookCreate(BorrowedBookBase):
    pass

class BorrowedBook(BorrowedBookBase):
    id: int
    returned_date: Optional[date] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None

class BorrowedBookWithUserInfo(BorrowedBookBase):
    id: int
    book: Book
    user: User

    class Config:
        orm_mode = True