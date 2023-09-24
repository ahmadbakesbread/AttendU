from app import app, engine, SessionLocal
from config import ProductionConfig
from Models import Base

if __name__ == '__main__':
    app.config.from_object(ProductionConfig) 
    app.run(debug=True)
