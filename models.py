from extensions import db, login_manager
from datetime import datetime
from flask_login import UserMixin


class Satellite(db.Model):
    # __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    Name = db.Column(db.String(50), unique = True)
    Norad_id = db.Column(db.Integer)
    OperatingFreq = db.Column(db.Numeric(precision=7, scale=4))
    TLERow1 = db.Column(db.String(length=80))
    TLERow2 = db.Column(db.String(length=80))
    TLEUpdateTime = db.Column(db.DateTime)
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
    ScheduledToReceive = db.Column(db.Boolean, default=True)
    SatetlliteName = db.Column(db.Integer, db.ForeignKey(Satellite.id))

    Report = db.relationship('Reports', backref="PassData", uselist=False, lazy = 'subquery')
    
    def __repr__(self):
        return f'{self.SatetlliteName} {self.AOS.strftime("%d-%m-%y %H:%M:%S")} {self.ScheduledToReceive}'
    
    def asDict(self):
        d = self.__dict__
        d.pop('_sa_instance_state',None)
        d.pop('Report')
        d['AOS'] = d['AOS'].astimezone()
        d['LOS'] = d['LOS'].astimezone()
        return d
    
    
class Reports(db.Model):
    __tablename__ = 'Reports'

    id = db.Column(db.Integer, db.ForeignKey(PassData.id), primary_key=True)
    size = db.Column(db.Integer)
    status = db.Column(db.Boolean, default=False)
    dataPath = db.Column(db.String(80))
    imagePath = db.Column(db.String(80))
    TLELine1 = db.Column(db.String(70))
    TLELine2 = db.Column(db.String(70))

    def __repr__(self):
        return f'{self.PassData.SatetlliteName} {self.PassData.AOS.strftime("%d-%m-%y %H:%M:%S")} {self.status}'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    # posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User( '{self.email}')"