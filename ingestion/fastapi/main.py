from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from dotenv import load_dotenv
from pathlib import Path

# .env project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD_PROJECT_CRAWL')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT_PROJECT_CRAWL')}/{os.getenv('POSTGRES_DB_PROJECT_CRAWL')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Ward(Base):
    __tablename__ = "wards"
    __table_args__ = {"schema": "raw"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String)
    city = Column(String)


Base.metadata.create_all(bind=engine)

class WardCreate(BaseModel):
    name: str
    district: Optional[str] = None
    city: Optional[str] = None


class WardsTextImport(BaseModel):
    data: str


app = FastAPI()


@app.post("/wards/import")
def import_wards(
    wards: List[WardCreate],
    db: Session = Depends(get_db)
):
    objects = [
        Ward(
            name=w.name,
            district=w.district,
            city=w.city
        )
        for w in wards
    ]

    db.add_all(objects)
    db.commit()

    return {
        "message": "Import wards successfully",
        "total": len(objects)
    }


@app.post("/wards/import-text")
def import_wards_from_text(
    payload: WardsTextImport,
    db: Session = Depends(get_db)
):
    """
    Example data:
    Thành Sen, Trần Phú, Cẩm Bình, Thạch Khê, Đồng  Tiến, Thạch Lạc
    """
    names = [x.strip() for x in payload.data.split(',')]
    
    parsed_wards = []
    errors = []
    
    for idx, name in enumerate(names, 1):
        if not name:
            continue
        
        parsed_wards.append({
            "name": name,
            "district": None,
            "city": None
        })
    
    # Tạo Ward objects
    objects = [
        Ward(
            name=w["name"],
            district=w["district"],
            city=w["city"]
        )
        for w in parsed_wards
    ]
    
    if objects:
        db.add_all(objects)
        db.commit()
    
    return {
        "message": "Import wards from text successfully",
        "total_imported": len(objects),
        "wards": [{"name": w.name, "id": w.id} for w in objects]
    }


@app.get("/wards")
def get_wards(db: Session = Depends(get_db)):
    return db.query(Ward).all()


@app.get("/wards/{ward_id}")
def get_ward_by_id(ward_id: int, db: Session = Depends(get_db)):
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        return {"error": "Ward not found", "id": ward_id}
    return ward


@app.put("/wards/{ward_id}")
def update_ward(ward_id: int, ward: WardCreate, db: Session = Depends(get_db)):
    existing_ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not existing_ward:
        return {"error": "Ward not found", "id": ward_id}
    
    existing_ward.name = ward.name
    existing_ward.district = ward.district
    existing_ward.city = ward.city
    db.commit()
    db.refresh(existing_ward)
    
    return {
        "message": "Ward updated successfully",
        "ward": existing_ward
    }


@app.patch("/wards/{ward_id}")
def partial_update_ward(
    ward_id: int,
    ward: WardCreate,
    db: Session = Depends(get_db)
):
    existing_ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not existing_ward:
        return {"error": "Ward not found", "id": ward_id}
    
    if ward.name:
        existing_ward.name = ward.name
    if ward.district:
        existing_ward.district = ward.district
    if ward.city:
        existing_ward.city = ward.city
    
    db.commit()
    db.refresh(existing_ward)
    
    return {
        "message": "Ward partially updated successfully",
        "ward": existing_ward
    }


@app.delete("/wards/{ward_id}")
def delete_ward(ward_id: int, db: Session = Depends(get_db)):
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        return {"error": "Ward not found", "id": ward_id}
    
    db.delete(ward)
    db.commit()
    
    return {
        "message": "Ward deleted successfully",
        "deleted_id": ward_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)