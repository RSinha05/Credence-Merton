from db.database import engine, Base
import db.models

print("Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
except Exception as e:
    print("Error:", e)
