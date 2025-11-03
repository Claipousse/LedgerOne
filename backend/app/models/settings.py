'''
Sert à définir les paramètres globaux de l'application via une table Settings
'''
from sqlalchemy import Column, Integer, Float, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base

class Settings(Base):
    '''
    Settings est une table avec une seule ligne (id=1) pour stocker les paramètres globaux
    Permet aussi de contenir le budget mensuel global (optionnel)
    '''
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=False, default=1)
    global_monthly_budget = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) #onupdate met à jour à chaque modif

    # Contraintes
    __table_args__ = (
        CheckConstraint('id = 1', name='check_single_row'), #Il doit n'y avoir qu'une seule ligne
        CheckConstraint(
            'global_monthly_budget IS NULL OR global_monthly_budget >= 0', #Budget soit nul soit positif, mais pas négatif
            name='check_global_budget_positive'
        ),
    )

    def __repr__(self): #Parametre l'affichage d'un objet Settings (en l'occurence on affiche le budget global)
        return f"<Settings(global_budget={self.global_monthly_budget})>"
    
    def to_dict(self):
        return {
            "global_monthly_budget": self.global_monthly_budget,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }