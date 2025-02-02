from database import SessionLocal, User, pwd_context

admin_created_successfully = False

def create_admin_user(username: str, password: str):
    global admin_created_successfully
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        print("Admin user already exists")
        return

    hashed_password = pwd_context.hash(password)

    admin_user = User(username=username, hashed_password=hashed_password, is_admin=True)
    db.add(admin_user)
    db.commit()
    print(f"Admin user '{username}' created successfully")
    admin_created_successfully = True

while not admin_created_successfully:
    username_input = input("Enter admin username > ")
    password_input = input("Enter admin password > ")
    create_admin_user(username_input, password_input)
