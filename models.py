from app import db
from datetime import datetime


class Satellite(db.Model):
    # __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    Name = db.Column(db.String(50), unique = True)
    Passes = db.relationship('PassData', backref = 'Passes')
    """_summary_
    Norad ID integer
    operating frequency float 4 decimal
    
    """
    
    def __repr__(self):
        return f'{self.Name}'

class PassData(db.Model):
    # __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    AOS = db.Column(db.DateTime, index=True)
    LOS = db.Column(db.DateTime)
    maxElevation = db.Column(db.Integer)
    ScheduledToReceive = db.Column(db.Boolean, default=False)
    SatetlliteName = db.Column(db.Integer, db.ForeignKey(Satellite.id))
    
    def __repr__(self):
        return f'{self.SatetlliteName} {self.AOS.strftime("%d-%m-%y %H:%M:%S")} {self.ScheduledToReceive}'
