from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas, security, recommendations
from datetime import date

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Book).offset(skip).limit(limit).all()

def create_book(db: Session, book: schemas.BookCreate):
    try:
        db_book = models.Book(**book.dict())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except IntegrityError:
        db.rollback()
        return None

def update_book(db: Session, book_id: int, book: schemas.BookCreate):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        for key, value in book.dict().items():
            setattr(db_book, key, value)
        try:
            db.commit()
            db.refresh(db_book)
            return db_book
        except IntegrityError:
            db.rollback()
            return None
    return None

def delete_book(db: Session, book_id: int):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
    return db_book

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = security.get_password_hash(user.password)
        db_user = models.User(full_name=user.full_name, email=user.email, hashed_password=hashed_password, role=user.role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        return None

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        if user.full_name is not None:
            db_user.full_name = user.full_name
        if user.email is not None:
            db_user.email = user.email
        if user.password is not None:
            db_user.hashed_password = security.get_password_hash(user.password)
        if user.role is not None:
            db_user.role = user.role
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            return None
    return None

def create_borrowed_book(db: Session, borrowed_book: schemas.BorrowedBookCreate):
    try:
        db_borrowed_book = models.BorrowedBook(**borrowed_book.dict())
        db.add(db_borrowed_book)
        db.commit()
        db.refresh(db_borrowed_book)
        return db_borrowed_book
    except IntegrityError:
        db.rollback()
        return None

def get_borrowed_books_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.BorrowedBook).filter(models.BorrowedBook.user_id == user_id, models.BorrowedBook.returned_date is None).offset(skip).limit(limit).all()

def return_borrowed_book(db: Session, borrowed_book_id: int):
    db_borrowed_book = db.query(models.BorrowedBook).filter(models.BorrowedBook.id == borrowed_book_id).first()
    if db_borrowed_book:
        db_borrowed_book.returned_date = date.today()
        db.commit()
        db.refresh(db_borrowed_book)
    return db_borrowed_book

def get_all_borrowed_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BorrowedBook).offset(skip).limit(limit).all()

def get_borrowed_books_with_user_info(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BorrowedBook).join(models.User).join(models.Book)
    if user_id:
        query = query.filter(models.BorrowedBook.user_id == user_id)
    return query.offset(skip).limit(limit).all()

def search_books(db: Session, title: str = None, author: str = None, isbn: str = None, genre: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Book)
    if title:
        query = query.filter(models.Book.title.contains(title))
    if author:
        query = query.filter(models.Book.author.contains(author))
    if isbn:
        query = query.filter(models.Book.isbn.contains(isbn))
    if genre:
        query = query.filter(models.Book.genre.contains(genre))
    return query.offset(skip).limit(limit).all()

def get_borrowed_history_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.BorrowedBook).filter(models.BorrowedBook.user_id == user_id).offset(skip).limit(limit).all()

def renew_borrowed_book(db: Session, borrowed_book_id: int, new_due_date: date):
    db_borrowed_book = db.query(models.BorrowedBook).filter(models.BorrowedBook.id == borrowed_book_id).first()
    if db_borrowed_book:
        db_borrowed_book.due_date = new_due_date
        db.commit()
        db.refresh(db_borrowed_book)
    return db_borrowed_book

def get_recommendations(db: Session, user_id: int, limit: int = 10):
    user_borrowed_books = db.query(models.Book).join(models.BorrowedBook).filter(models.BorrowedBook.user_id == user_id).all()
    all_books = db.query(models.Book).all()
    
    recommended_books = recommendations.get_recommendations(user_borrowed_books, all_books)
    
    return recommended_books[:limit]