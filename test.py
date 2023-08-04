# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 15:52:37 2023

@author: Abdullah
"""

from models import Satellite, PassData
from app import app, db
from sdrangel_requests import *
from tzlocal import get_localzone
from datetime import datetime, timedelta
from sqlalchemy import and_,func
from celery import shared_task

#%%
"""
#%%

#  Populating the Satellite Data table
with app.app_context():
    db.create_all()
    Satellite_names = {'NOAA 15':[25338, 137.620], 
                       'NOAA 18':[28654, 137.9125],
                       'NOAA 19':[33591, 137.100]}
    for name in Satellite_names:
        satellite = Satellite(Name= name, 
                              Norad_id= Satellite_names[name][0],
                              OperatingFreq= Satellite_names[name][1])
        db.session.add(satellite)
        try:
            db.session.commit()
            print(f"{name} added!")
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")

#%%

# Fetching passes from SDRangel and adding to database with proper timeformat
with app.app_context():
    Sat = Satellite.query.filter_by(Name="NOAA 19").first()
    passes = get_satellite_passes(str(Sat))
    for pass1 in passes:
        db.session.add(PassData(AOS = datetime.strptime(pass1['aos'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(),
                  LOS = datetime.strptime(pass1['los'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(),
                  maxElevation = int(pass1['maxElevation']),
                  SatetlliteName = str(Sat)))
    try:
        db.session.commit()
        print(f"Pass added!")
    except Exception as e:
        db.session.rollback()
        print(f"Commit Failed. Error: {e}")
        
#%%

# Deleting passes with pk
for i in range(55,91):
    with app.app_context():
        d = db.get_or_404(PassData, i)
        db.session.delete(d)
        db.session.commit()

           

#%%

# Filtering passdata that needs to be showed
with app.app_context():
    data = PassData.query.filter(and_(PassData.AOS >= datetime.now(), 
                                         PassData.ScheduledToReceive)).all()
    print(data.AOS)
    
#%%
"""
#%%

# adding new passes only after checking that they are not already present
@shared_task(name='updateDB')
def updateDB():
    with app.app_context():
        Satellites = Satellite.query.all()
        for sat in Satellites:
            sat_name = sat.Name
            print(sat_name)
            passes = get_satellite_passes(sat_name)
            twomins= timedelta(minutes=2)
            for p in passes:
                aos = datetime.strptime(p['aos'],'%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                los = datetime.strptime(p['los'],'%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                data = PassData.query.filter(and_(PassData.AOS <= aos+twomins,
                                                  PassData.AOS >= aos-twomins,
                                                  PassData.SatetlliteName == sat_name)).all()
                print(data)
                if data and data[0].AOS.time() != aos.time():
                    data[0].AOS = aos
                elif data and data[0].LOS.time() != los.time():
                    data[0].LOS = los
                elif not data:
                    db.session.add(PassData(AOS=aos,
                                   LOS=los,
                                   maxElevation=int(p['maxElevation']),
                                   SatetlliteName=sat_name))
                    try:
                        db.session.commit()
                        print(f"Pass added!")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Commit Failed. Error: {e}") 
        
        

#%%
def parse_table(data):
    return [{k:(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()).strftime('%d-%m-%y %H:%M:%S')
                if isinstance(v,str) else int(v)) for k,v in i.items()} for i in data]


# with app.app_context():
#     d = PassData.query.filter(and_(PassData.AOS <= datetime.now(),
#                                 PassData.SatetlliteName == "NOAA 19")).all()
#     db.session.delete(d)
#     db.session.commit()

#%%
def schedule():
    for i in [147, 117, 134, 114]:
        with app.app_context():
            d = db.get_or_404(PassData, i)
            d.ScheduledToReceive=True
            db.session.commit()

#%%
def convertodict(d):
    d = d.__dict__
    d.pop('_sa_instance_state',None)
    d['AOS'] = d['AOS'].astimezone()
    d['LOS'] = d['LOS'].astimezone()
    return d