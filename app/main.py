
from fastapi import Depends, FastAPI, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from . import crud, models, schemas, dependencies, security
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Management API")

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/", tags=["Home"], description="Redirects to the API documentation.")
def read_root():
    return RedirectResponse(url="/docs")

@app.post("/login", 
          response_model=schemas.Token, 
          tags=["Authentication"], 
          description="Authenticate user and return an access token.")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", 
          response_model=schemas.User,
          tags=["Users"], 
          description="Register a new user.")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, user=user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_user


@app.get("/users/{user_id}",
         response_model=schemas.User, 
         tags=["Users"],
         description="Get user details by user ID.")
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/me/",
         response_model=schemas.User,
         tags=["Users"], description="Update the current user's profile.")
def update_users_me(
    user: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_user)
):
    db_user = crud.update_user(db=db, user_id=current_user.id, user=user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered or user not found")
    return db_user


@app.put("/users/{user_id}", 
         response_model=schemas.User, 
         tags=["Users"], 
         description="Update a user's profile by user ID. Staff only.")
def update_user_by_id(
    user_id: int, 
    user: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    db_user = crud.update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found or email already registered")
    return db_user


@app.get("/users/me/", 
         response_model=schemas.User, 
         tags=["Users"], 
         description="Get the current user's profile.")
def read_users_me(current_user: models.User = Depends(dependencies.get_current_user)):
    return current_user


@app.get("/users/me/borrowed_books/", 
         response_model=list[schemas.BorrowedBook], 
         tags=["Users"], 
         description="List all books currently borrowed by the authenticated user.")
def read_my_borrowed_books(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    borrowed_books = crud.get_borrowed_books_by_user(db, user_id=current_user.id)
    return borrowed_books


@app.get("/borrowed_books/staff/", 
         response_model=list[schemas.BorrowedBookWithUserInfo], 
         tags=["Borrowed Books"], 
         description="List all borrowed books with user and book details. Staff only.")
def read_all_borrowed_books_with_user_info(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(dependencies.get_current_staff_user),
    db: Session = Depends(get_db)
):
    borrowed_books = crud.get_borrowed_books_with_user_info(db, user_id=user_id, skip=skip, limit=limit)
    return borrowed_books


@app.get("/borrowed_books/all/", 
         response_model=list[schemas.BorrowedBook], 
         tags=["Borrowed Books"], 
         description="List all borrowed books in the system. Staff only.")
def read_all_borrowed_books(
    current_user: models.User = Depends(dependencies.get_current_staff_user),
    db: Session = Depends(get_db)
):
    borrowed_books = crud.get_all_borrowed_books(db)
    return borrowed_books


@app.post("/books/", 
          response_model=schemas.Book, 
          tags=["Books"], 
          description="Add a new book to the library. Staff only.")
def create_book(
    book: schemas.BookCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    db_book = crud.create_book(db=db, book=book)
    if db_book is None:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    return db_book


@app.put("/books/{book_id}", 
         response_model=schemas.Book, 
         tags=["Books"], 
         description="Update book details by book ID. Staff only.")
def update_book(
    book_id: int, book: schemas.BookCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    db_book = crud.update_book(db=db, book_id=book_id, book=book)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found or ISBN already exists")
    return db_book


@app.delete("/books/{book_id}", 
            tags=["Books"], 
            description="Delete a book from the library by book ID. Staff only.")
def delete_book(
    book_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    db_book = crud.delete_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@app.get("/books/", 
         response_model=list[schemas.Book], 
         tags=["Books"], 
         description="List all books in the library. Supports pagination.")
def read_books(skip: int = 0, 
               limit: int = 100, 
               db: Session = Depends(get_db)):
    books = crud.get_books(db, skip=skip, limit=limit)
    return books


@app.get("/books/{book_id}", 
         response_model=schemas.Book, 
         tags=["Books"], 
         description="Get details of a book by book ID.")
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book


@app.get("/books/search/", 
         response_model=list[schemas.Book], 
         tags=["Books"], 
         description="Search for books by title, author, ISBN, or genre. Supports pagination.")
def search_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    genre: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    books = crud.search_books(db, title=title, author=author, isbn=isbn, genre=genre, skip=skip, limit=limit)
    return books


@app.post("/borrow/", 
          response_model=schemas.BorrowedBook, 
          tags=["Borrowed Books"], 
          description="Borrow a book. Only authenticated users can borrow books.")
def borrow_book(
    borrowed_book: schemas.BorrowedBookCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_user)
):
    db_book = crud.get_book(db, book_id=borrowed_book.book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db_user = crud.get_user(db, user_id=borrowed_book.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_borrowed_book = crud.create_borrowed_book(db=db, borrowed_book=borrowed_book)
    if db_borrowed_book is None:
        raise HTTPException(status_code=400, detail="Book is already borrowed by this user")
    return db_borrowed_book


@app.put("/borrow/{borrowed_book_id}/renew", 
         response_model=schemas.BorrowedBook, 
         tags=["Borrowed Books"], 
         description="Renew a borrowed book. Only authenticated users can renew their borrowed books.")
def renew_borrow_book(
    borrowed_book_id: int, 
    new_due_date: date, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_user)
):
    db_borrowed_book = crud.renew_borrowed_book(db, borrowed_book_id=borrowed_book_id, new_due_date=new_due_date)
    if db_borrowed_book is None:
        raise HTTPException(status_code=404, detail="Borrowed book not found")
    return db_borrowed_book


@app.put("/borrow/{borrowed_book_id}/return", 
         response_model=schemas.BorrowedBook, 
         tags=["Borrowed Books"], 
         description="Return a borrowed book by its ID. Staff only.")
def return_book(
    borrowed_book_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    db_borrowed_book = crud.return_borrowed_book(db, borrowed_book_id=borrowed_book_id)
    if db_borrowed_book is None:
        raise HTTPException(status_code=404, detail="Borrowed book not found")
    return db_borrowed_book


@app.get("/users/me/borrow_history/", 
         response_model=list[schemas.BorrowedBook], 
         tags=["Users"], 
         description="List all borrowed books (including returned ones) for the authenticated user.")
def read_my_borrow_history(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    borrowed_books = crud.get_borrowed_history_by_user(db, user_id=current_user.id)
    return borrowed_books


@app.get("/users/me/recommendations/", 
         response_model=list[schemas.Book], 
         tags=["Users"], 
         description="Get book recommendations for the authenticated user.")
def get_my_recommendations(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    recommendations = crud.get_recommendations(db, user_id=current_user.id)
    return recommendations


@app.get("/users/{user_id}/borrow_history/", 
         response_model=list[schemas.BorrowedBook], 
         tags=["Users"], 
         description="List all borrowed books (including returned ones) for a specific user. Staff only.")
def read_user_borrow_history(
    user_id: int, 
    current_user: models.User = Depends(dependencies.get_current_staff_user),
    db: Session = Depends(get_db)
):
    borrowed_books = crud.get_borrowed_history_by_user(db, user_id=user_id)
    return borrowed_books
