import string
import random

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from database import SessionLocal, URL

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class URLRequest(BaseModel):
    long_url: HttpUrl

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits # abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
    random_characters = random.choices(characters, k=length) # ['8', 'n', 'p', 'O', 'u', 'c']
    return ''.join(random_characters) # 8npOuc


@app.post("/shorten/")
def shorten_url(request: URLRequest, db: Session = Depends(get_db)):
    """
    - generate short code
    - extract the long url from the request
    - generate table entry with the short code and the long url
    - add and commit the table entry to the database
    - return the short url jason
    """
    short_code = generate_short_code()
    long_url = str(request.long_url)
    db_url_entry = URL(shortcode=short_code, long_url=long_url)
    db.add(db_url_entry)
    db.commit()
    return {"short_url": f"http://127.0.0.1:8000/{short_code}"}


@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """
    - query the database to filter based on the short code
    - if no result found, return 404 error
    - if there is result, increase visit_count by one, commit this change to the database
    - redirect to the long_url
    """
    db_url_search_result = db.query(URL).filter(URL.shortcode == short_code).first()

    if not db_url_search_result:
        raise HTTPException(status_code=404, detail="No URL found with this short URL")

    db_url_search_result.visit_count += 1
    db.commit()

    return RedirectResponse(url=str(db_url_search_result.long_url))


@app.get("/{short_code}/stats")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    """
    - query the database to filter based on the short code
    - if no result found, return 404 error
    - if there is result, return the short_url, long_url and visit_count
    """
    db_url_search_result = db.query(URL).filter(URL.shortcode == short_code).first()

    if not db_url_search_result:
        raise HTTPException(status_code=404, detail="No URL found with this short URL")

    return {"short_url": f"http://127.0.0.1:8000/{short_code}",
            "long_url": str(db_url_search_result.long_url),
            "visit_count": db_url_search_result.visit_count}

