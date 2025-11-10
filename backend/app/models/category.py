'''
Sert à établir ce qu'est une catégorie
'''

from sqlalchemy import Column, Integer, String, Float, CheckConstraint
from sqlalchemy.orm import relationship #Pour gérer les FK
from app.database import Base

class Category(Base): #Hérite de superclasse Base et de ses propriétés (Connexion à BDD,...)
    '''
    Une catégorie est composée de :
    - un id (géré automatiquement)
    - Un nom/titre (Alimentation, Transport, ...)
    - Une couleur (optionnelle)
    - Un budget mensuel (optionnel)
    '''
    __tablename__ = "categories"
    id = Column(Integer, primary_key = True, index = True, autoincrement=True)
    name = Column(String, unique =True, nullable= False, index = True) #On index pour pouvoir faire des recherches par nom
    color = Column(String, nullable=True) #String pour code héxadécimal
    monthly_budget = Column(Float, nullable=True)

    #Relation
    transactions = relationship(
        "Transaction",
        back_populates="category", #Bidirectionnel
    )

    #Contraintes
    __table_args__ = (
        CheckConstraint(
            'monthly_budget IS NULL OR monthly_budget >= 0', #Le budget doit être supérieur ou égal à 0
            name='check_monthly_budget_positive' #Sinon on indique cette erreur
        ),
    )

    def __repr__(self): #Parametre l'affichage d'un objet Category (sinon ça mettrais son emplacement mémoire)
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    def to_dict(self): #Convertir en dictionnaire
        return {
            "id":self.id,
            "name":self.name,
            "color":self.color,
            "monthly_budget":self.monthly_budget
        }



