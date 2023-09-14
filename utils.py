# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 15:52:37 2023

@author: Abdullah
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func
from tzlocal import get_localzone

from app import app
from extensions import db, scheduler
from models import PassData, Satellite
# from app import db, scheduler

# %% Populating the Satellite Data table


def pop_sats():
    """  
    Returns
    -------
    None.

    """
    with app.app_context():
        db.create_all()
        Satellite_names = {'NOAA 15': [25338, 137.620],
                           'NOAA 18': [28654, 137.9125],
                           'NOAA 19': [33591, 137.100]}
        for name in Satellite_names:
            satellite = Satellite(Name=name,
                                  Norad_id=Satellite_names[name][0],
                                  OperatingFreq=Satellite_names[name][1])
            db.session.add(satellite)
            try:
                db.session.commit()
                print(f"{name} added!")
            except Exception as e:
                db.session.rollback()
                print(f"Commit Failed. Error: {e}")


# %%
"""_sats
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
    
"""



# %%
def parse_table(data):
    return [{k: (datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()).strftime('%d-%m-%y %H:%M:%S')
                 if isinstance(v, str) else int(v)) for k, v in i.items()} for i in data]


# with app.app_context():
#     d = PassData.query.filter(and_(PassData.AOS <= datetime.now(),
#                                 PassData.SatetlliteName == "NOAA 19")).all()
#     db.session.delete(d)
#     db.session.commit()

# %% Set Scheduled to Receive to True
def schedule():
    for i in [160, 172, 181, 163, 164, 175, 184, 176]:
        with app.app_context():
            d = db.get_or_404(PassData, i)
            d.ScheduledToReceive = True
            db.session.commit()

# %% delete passData with pk


def delete():
    for i in [88]:
        d = PassData.query.get_or_404(i)
        db.session.delete(d)
        db.session.commit()

# %%


def convertodict(d):
    d = d.__dict__
    d.pop('_sa_instance_state', None)
    d['AOS'] = d['AOS'].astimezone()
    d['LOS'] = d['LOS'].astimezone()
    return d


# %% get two line element

# a = get_tle(25338)
