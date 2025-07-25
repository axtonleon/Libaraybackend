
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def get_recommendations(user_borrowed_books, all_books):
    if not user_borrowed_books:
        return []

    all_books_df = pd.DataFrame([book.__dict__ for book in all_books])
    user_borrowed_books_df = pd.DataFrame([book.__dict__ for book in user_borrowed_books])

    all_books_df['content'] = all_books_df['title'] + ' ' + all_books_df['author'] + ' ' + all_books_df['genre']
    
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_books_df['content'])
    
    user_profile = tfidf_vectorizer.transform(user_borrowed_books_df['title'])
    
    cosine_sim = cosine_similarity(user_profile, tfidf_matrix)
    
    recommendation_scores = cosine_sim.mean(axis=0)
    
    recommended_book_indices = recommendation_scores.argsort()[::-1]
    
    recommended_books = []
    for idx in recommended_book_indices:
        if all_books[idx].id not in user_borrowed_books_df['id'].tolist():
            recommended_books.append(all_books[idx])
    
    return recommended_books
