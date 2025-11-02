'''
Sert à établir ce qu'est une transaction
'''

from sqlalchemy import Column, Integer, Float, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    '''
    Une transaciton est composée de :
    - Un id (géré automatiquement)
    - Une date (Date où la transaction a eu lieu)
    - Une description du paiement (ex: Abonnement Netflix, Course chez Carrefour, ...)
    - Un montant en euros
    - Une catégorie auquel il appartient (optionnel)
    - Une date de création
    '''
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    date = Column(Date, nullable= False, index=True) #Format AAAA-MM-JJ
    description = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    # ForeignKey : Lien vers la table categories
    # ondelete="SET NULL" : Si catégorie supprimée, mettre category_id à NULL (garder la transaction)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) #Format AAAA-MM-JJ HH:MM:SS

    #Relation
    category = relationship("Category", back_populates="transactions")

    # Index composé avec date + catégorie (permet recherche rapide par date & catégorie simultanément)
    __table_args__ = (Index('ix_transactions_date_category', 'date', 'category_id')),

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount})>"
    
    def to_dict(self, include_category=True):
        result = {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "amount": self.amount,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_category and self.category: #Si jamais la transaction appartient à une catégorie, on affiche des infos de la catégorie auquel elle appartient
            result["category_name"] = self.category.name
            result["category_color"] = self.category.color
        
        return result




