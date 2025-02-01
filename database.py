from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./shortener.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
############################
class URL(Base):
    __tablename__ = "urls"

    shortcode = Column(String, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    visit_count= Column(Integer, default=0)

Base.metadata.create_all(bind=engine)