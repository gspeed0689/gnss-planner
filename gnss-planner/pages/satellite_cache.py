from sqlalchemy import DateTime, Text, Integer
from sqlalchemy import insert, select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class satelliteBase(DeclarativeBase):
    pass

class satelliteCache(satelliteBase):
    __tablename__ = "satellite_cache"
    pk_satellite_cache: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_datetime: Mapped[datetime] = mapped_column(DateTime)
    content: Mapped[str] = mapped_column(Text)

engine = create_engine("sqlite:///./satellite_cache.sqlite")

satelliteBase.metadata.create_all(engine)

def create_cache_record(request_time, result):
    with Session(engine) as session:
        stmt = insert(satelliteCache)
        stmt = stmt.values(access_datetime=request_time, content=result)
        EXEC = session.execute(stmt)
        session.commit()

def get_last_cache_record():
    with Session(engine) as session:
        stmt = select(satelliteCache)
        stmt = stmt.order_by(satelliteCache.access_datetime.desc())
        result = session.execute(stmt).first()
        # print(result)
        # print(type(result))
    if result:
        return result[0]
    else:
        return None