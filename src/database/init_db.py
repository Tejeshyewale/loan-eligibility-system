from .db import engine
from .models import Base

print("Creating database tables...")
Base.metadata.create_all(engine)
print("Database initialized successfully!")
