from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(String, primary_key=True)
    salt = Column(String)
    key = Column(String)
    tweets = relationship('Tweet', back_populates='author')


class Tweet(Base):
    __tablename__ = 'tweet'
    id = Column(Integer, primary_key=True)
    author_id = Column(String, ForeignKey('user.id'))
    author = relationship('User', back_populates='tweets')
    text = Column(String, nullable=False)


if __name__ == '__main__':
    engine = create_engine('sqlite:///cottorro.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    conn = engine.connect()
    conn.execute('PRAGMA foreign_keys = ON;')
    yo = User()
    yo.id = 'Ark'
    yo.key = 'pass'
    yo.salt = '-098adsf6bb5h50adf'
    session.add(yo)
    t1 = Tweet()
    t1.author_id = 'Ark'
    t1.text = 'Esto es una prueba'
    session.add(t1)
    t2 = Tweet()
    t2.author_id = 'Ark'
    t2.text = 'Esto es otra prueba'
    session.add(t2)
    for ta in session.query(Tweet).all():
        print(ta.text, ta.id, ta.author_id, ta.author)
    session.commit()
