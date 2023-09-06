from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from application import Base
from flask_login import UserMixin

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(Enum('User', 'Admin'), nullable=False)
    account_status = Column(Enum('Pending', 'Approved'), nullable=False)

    votes = relationship('Vote', back_populates='user')


class Car(Base):
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True)
    car_name = Column(String(255), nullable=False)
    car_details = Column(String(1500))
    image_url = Column(String(255))
    created_by = Column(Integer, ForeignKey('users.id'))

    votes = relationship('Vote', back_populates='car')


class Vote(Base):
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    vote_status = Column(Enum('Cast', 'Unvoted'), nullable=False)

    user = relationship('User', back_populates='votes')
    car = relationship('Car', back_populates='votes')
