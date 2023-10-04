# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 15:52:37 2023

@author: Abdullah
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func
# from tzlocal import get_localzone
from app import app
from extensions import db, scheduler
from models import PassData, Satellite, Reports
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
    with app.app_context():
        for i in [491]:
            d = Reports.query.get_or_404(i)
            db.session.delete(d)
            db.session.commit()

# %%


def convertodict(d):
    d = d.__dict__
    d.pop('_sa_instance_state', None)
    d['AOS'] = d['AOS'].astimezone()
    d['LOS'] = d['LOS'].astimezone()
    return d

# %%


def getmfile(search_dir, pk):
    """  
    function that finds file that was modified most recently
    
    Parameters
    ----------
    search_dir : string
        Path of the directory that needs to be searched.
    pk : int
        primary key of the pass for which data is being searched

    Returns
    -------
    files : list
        returns a list of files sorted by time closest to Pass LOS

    """

    import os
    
    with app.app_context():
        p = db.get_or_404(PassData, pk)
        time = p.LOS## - timedelta(hours=3) ## The timedelta is added for timzone correction!
    files = list(os.scandir(search_dir))
    
    print(time)
    # return files
    files = sorted(files, key=lambda x: (datetime.fromtimestamp(x.stat().st_mtime) - time).seconds)
    return files[0]


# Impath = 'C:/Users/Abdullah/Desktop/NOAA-Images/'
# dpath = 'C:/Users/Abdullah/Desktop/NOAA-wav/'
# Impath = "C:/Users/DELL/Documents/NOAA-Images/"

# I = getmfile(Impath, 441)
# d = getmfile(dpath, 441)
# "C:/Users/DELL/Documents/NOAA-Images/apt_NOAA_19_20231003_0135.png"

def create_report(dpath, Impath, pk):
    with app.app_context():
        p = db.get_or_404(PassData, pk)
        Imfile = getmfile(Impath, pk)
        dfile =  getmfile(dpath,491)
        twomins = timedelta(seconds=120)
        dmtime = datetime.fromtimestamp(dfile.stat().st_mtime)
        Imtime = datetime.fromtimestamp(Imfile.stat().st_mtime)
        time = p.LOS## - timedelta(hours=3)
        ## The timedelta is added for timzone correction
        ## must be removed!
        
        if (time - dmtime) < twomins:
            dfsize = round(dfile.stat().st_size/int(1<<20))
            dfile = dfile.path
        else:
            dfile = None
            dfsize = None
            
        if (time - Imtime) < twomins:
            Imfilepath = Imfile.path
        else:
            Imfilepath = None
            
        if (Imtime - dmtime) < twomins and dfile != None and Imfilepath != None:
            pstatus = True
        else:
            pstatus = False
        
        r = Reports(id = p.id,
                    size = dfsize,
                    status = pstatus,
                    dataPath = dfile,
                    imagePath = Imfilepath)
        db.session.add(r)
        try:
            db.session.commit()
            print("Report added!")
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")


#%%
# utils.create_report(dpath,Impath,491)
with app.app_context():
    r = db.get_or_404(Reports,491)
    r.imagePath = "C:/Users/DELL/Documents/NOAA-Images/apt_NOAA_19_20231003_0135.png"
    r.status = True
    db.session.commit()
    
with app.app_context():
    r = db.get_or_404(Reports,491)
    print(r)


#%%

# from datetime import datetime
# from sqlalchemy import and_

# from app import app
# from models import PassData, Reports
# from utils import create_report

# fromdate = datetime(2023, 10, 2)
# todate = datetime(2023, 10, 3)

# with app.app_context():
#     passes = PassData.query.filter(and_(PassData.LOS >= fromdate), PassData.LOS <= todate).all()
# p = [i.id for i in passes]

# dpath = "D:/NOAA-wav/"
# Impath = "C:/Users/DELL/Documents/NOAA-Images/"

# for i in p:
#     create_report(dpath, Impath, i)

# create_report(507)
# %% get two line element

# a = get_tle(25338)
