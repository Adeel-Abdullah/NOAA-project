# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 15:52:37 2023

@author: Abdullah
"""

from models import Satellite, PassData
from app import app, db
from sdrangel_requests import *
from tzlocal import get_localzone
from datetime import datetime
 from sqlalchemy import and_,func

with app.app_context():
    db.create_all()
    Satellite_names = ['NOAA 15', 'NOAA 18', 'NOAA 19']
    for name in Satellite_names:
        satellite = Satellite(Name= name)
        db.session.add(satellite)
        try:
            db.session.commit()
            print(f"{name} added!")
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")

#%%

# with app.app_context():
#     Sat = Satellite.query.filter_by(Name="NOAA 19").first()
#     passes = get_satellite_passes(str(Sat))
#     for pass1 in passes:
#         db.session.add(PassData(AOS = datetime.strptime(pass1['aos'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()),
#                  LOS = datetime.strptime(pass1['los'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()),
#                  maxElevation = int(pass1['maxElevation']),
#                  SatetlliteName = str(Sat)))
#     try:
#         db.session.commit()
#         print(f"Pass added!")
#     except Exception as e:
#         db.session.rollback()
#         print(f"Commit Failed. Error: {e}")
        
#%%

with app.app_context():
    data = PassData.query.filter(PassData.SatetlliteName== "NOAA 18").all()
    print(data)