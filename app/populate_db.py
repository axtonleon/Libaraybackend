from sqlalchemy.orm import Session
from faker import Faker
from datetime import date, timedelta
import random

from . import crud, models, schemas
from .database import SessionLocal, engine
from .security import get_password_hash

def create_fake_data(db: Session, num_users: int = 50, num_books: int = 50):
    fake = Faker()

    # Create tables
    models.Base.metadata.create_all(bind=engine)

    # Create fake users
    print(f"Creating {num_users} fake users...")
    for _ in range(num_users):
        full_name = fake.name()
        email = fake.unique.email()
        password = "password" # All users will have 'password' as their password for simplicity
        role = random.choice(["staff", "student"])
        user_create = schemas.UserCreate(
            full_name=full_name,
            email=email,
            password=password,
            role=role
        )
        crud.create_user(db, user_create)
    print("Fake users created.")

    # Create fake books
    print(f"Creating {num_books} fake books...")
    genres = ["Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller", "Romance", "Horror", "Historical Fiction", "Biography", "Self-Help", "Poetry", "Young Adult", "Children's", "Non-Fiction"]
    for _ in range(num_books):
        title = fake.sentence(nb_words=random.randint(3, 7)).replace(".", "")
        author = fake.name()
        isbn = fake.unique.isbn13()
        genre = random.choice(genres)
        book_create = schemas.BookCreate(
            title=title,
            author=author,
            isbn=isbn,
            genre=genre
        )
        crud.create_book(db, book_create)
    print("Fake books created.")

    # Create some fake borrowed books for different use cases
    print("Creating some fake borrowed books...")
    users = db.query(models.User).all()
    books = db.query(models.Book).all()

    # Ensure we have enough users and books to create borrowed entries
    if len(users) > 5 and len(books) > 5:
        # User with multiple borrowed books
        user1 = random.choice(users)
        for _ in range(random.randint(2, 5)):
            book = random.choice(books)
            due_date = date.today() + timedelta(days=random.randint(7, 30))
            borrowed_book_create = schemas.BorrowedBookCreate(
                book_id=book.id,
                user_id=user1.id,
                due_date=due_date
            )
            crud.create_borrowed_book(db, borrowed_book_create)

        # User with overdue book
        user2 = random.choice([u for u in users if u.id != user1.id])
        book2 = random.choice([b for b in books if b.id != book.id])
        overdue_date = date.today() - timedelta(days=random.randint(1, 10))
        borrowed_book_create_overdue = schemas.BorrowedBookCreate(
            book_id=book2.id,
            user_id=user2.id,
            due_date=overdue_date
        )
        crud.create_borrowed_book(db, borrowed_book_create_overdue)

        # User with returned book
        user3 = random.choice([u for u in users if u.id != user1.id and u.id != user2.id])
        book3 = random.choice([b for b in books if b.id != book.id and b.id != book2.id])
        due_date_returned = date.today() + timedelta(days=random.randint(7, 14))
        borrowed_book_create_returned = schemas.BorrowedBookCreate(
            book_id=book3.id,
            user_id=user3.id,
            due_date=due_date_returned
        )
        db_borrowed = crud.create_borrowed_book(db, borrowed_book_create_returned)
        if db_borrowed:
            crud.return_borrowed_book(db, db_borrowed.id)

    print("Fake borrowed books created.")
    print("Database population complete.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        create_fake_data(db)
    finally:
        db.close()
