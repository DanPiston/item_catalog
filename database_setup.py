from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

#class for broad topics
class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)

    #return serialized data
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            }

class Item(Base):

    __tablename__ = 'item'

    name = Column(String(80), nullable= False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
        }

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)