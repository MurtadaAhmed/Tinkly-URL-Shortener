import string
import random
import os
from calendar import error

from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import SessionLocal, URL, User, pwd_context
from starlette.middleware.sessions import SessionMiddleware

WEBSITE_URL = os.getenv("WEBSITE_URL","http://127.0.0.1")
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!@#$#%%^^&&*(*()_+_)(*&^%")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Get the current logged-in user from the session.
    If no username provided, it returns 401
    If the username is not in the database, it returns 401
    If the user is in the database, returns the user
    """
    username = request.session.get("username")
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    return user

class URLRequest(BaseModel):
    long_url: HttpUrl

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits # abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
    random_characters = random.choices(characters, k=length) # ['8', 'n', 'p', 'O', 'u', 'c']
    return ''.join(random_characters) # 8npOuc

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    current_user = None
    if username:
        current_user = db.query(User).filter(User.username == username).first()
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})

@app.post("/shorten/")
def shorten_url(request: URLRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    - generate short code
    - extract the long url from the request
    - generate table entry with the short code and the long url
    - add and commit the table entry to the database
    - return the short url jason
    """
    short_code = generate_short_code()
    long_url = str(request.long_url)
    owner_id = current_user.id if current_user else None
    db_url_entry = URL(shortcode=short_code, long_url=long_url, owner_id=owner_id)
    db.add(db_url_entry)
    db.commit()
    return {"short_url": f"{WEBSITE_URL}/{short_code}"}


@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db), request: Request = None):
    """
    - query the database to filter based on the short code
    - if no result found, return 404 error
    - if there is result, increase visit_count by one, commit this change to the database
    - if the request is coming from api, return json with long_url and visit_count
    - if the request is coming from the browser (UI), redirect to the long_url
    """
    db_url_search_result = db.query(URL).filter(URL.shortcode == short_code).first()

    if not db_url_search_result:
        raise HTTPException(status_code=404, detail="No URL found with this short URL")

    db_url_search_result.visit_count += 1
    db.commit()

    if request and "application" and "application/json" in request.headers.get("accept", ""):
        return {"long_url": str(db_url_search_result.long_url), "visit_count": db_url_search_result.visit_count}

    return RedirectResponse(url=str(db_url_search_result.long_url))


@app.get("/{short_code}/stats")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    """
    - query the database to filter based on the short code
    - if no result found, return 404 error
    - if there is result, return the short_url, long_url and visit_count as json
    """
    db_url_search_result = db.query(URL).filter(URL.shortcode == short_code).first()

    if not db_url_search_result:
        raise HTTPException(status_code=404, detail="No URL found with this short URL")

    return {"short_url": f"{WEBSITE_URL}/{short_code}",
            "long_url": str(db_url_search_result.long_url),
            "visit_count": db_url_search_result.visit_count}



# user authentication

@app.get("/register/")
def register_page(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register/")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Check the username against database.
    If the username already exists in the database, raise 400 status code
    If the username doesn't exist in the database, hash the password and add the username and hashed password to the
    database
    """
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        if "application/json" in request.headers.get("accept", ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        error = "Username already registered"
        return templates.TemplateResponse("register.html", {"request": request, "error": error})
    hashed_password = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    request.session["username"] = user.username
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login/", response_class=HTMLResponse)
def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})
@app.post("/login/")
def login(request: Request,username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Check the input username and the password against the database
    If either is none, raise 401 status code
    If there is a match, add the username in the session
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        if "application/json" in request.headers.get("accept", ""):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        error = "Incorrect username or password"
        return templates.TemplateResponse("login.html", {"request": request, "error": error})
    request.session["username"] = user.username
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout/")
def logout(request: Request):
    """
    Removes the user from the session (if exists) else just None if no user is logged in so no errors will occur
    Return success logout message
    """
    request.session.pop("username", None)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard/")
def dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the urls from the database for the current logged-in user
    Render the dashboard.html template, and send the request and the user_urls to it
    """
    if not current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    user_urls = db.query(URL).filter(URL.owner_id == current_user.id).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user_urls": user_urls, "current_user": current_user})


@app.get("/{short_code}/delete")
def delete_url(short_code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Search the database for match for the url to be deleted and the owner of it
    If there is no match, raise 404 status code
    If there is a match, delete the url from the database
    Redirect the user to the dashboard page
    """
    if not current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    db_url = db.query(URL).filter(URL.shortcode == short_code, URL.owner_id == current_user.id).first()
    if not db_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    db.delete(db_url)
    db.commit()
    return RedirectResponse(url="/dashboard/", status_code=status.HTTP_303_SEE_OTHER)



@app.get("/admin/")
def admin_panel(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    If guest user tries to access the admin page, get redirected to login page
    if non-admin user tries to access the admin page, returns 403 forbidden
    Query the database for all the users and all the urls, and render them with current_user to the admin page
    """
    if not current_user:
        return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")
    users = db.query(User).all()
    urls = db.query(URL).all()

    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "urls": urls, "current_user": current_user})


@app.post("/admin/user/delete/{user_id}")
def admin_delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Check if an admin tries to access the page
    if not, return 403
    if admin, query the database for that user
    if user not found return 404
    if user is found, delete it from the database and return back to admin page
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/user/edit/{user_id}")
def admin_edit_user(
        user_id: int,
        username: str = Form(...),
        password: str = Form(...),
        is_admin: bool = Form(False),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """
    check if admin is accessing the edit feature
    if not, return 403
    if admin, query the database for the user, make the change to username/password/is_admin
    return back to admin page
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.username = username
    if password:
        user.hashed_password = pwd_context.hash(password)
    user.is_admin = is_admin
    db.commit()
    return RedirectResponse(url="/admin/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/url/delete/{short_code}")
def admin_delete_url(short_code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    check if admin is accessing the delete url feature
    if not, return 403
    if admin, query the database for the url
    if url not found, return 404
    if url found, delete it and return back to admin page
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    url = db.query(URL).filter(URL.shortcode == short_code).first()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    db.delete(url)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/user/create")
def admin_create_user(username: str = Form(...),
                      password: str = Form(...),
                      is_admin: bool = Form(False),
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    check if admin is accessing the create user feature
    if not, return 403
    if admin, query the database to see if username already exist
    if username already exist, return 400
    if username is unique, hash the password and create new user
    return back to admin page
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
    hashed_password = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=status.HTTP_303_SEE_OTHER)
