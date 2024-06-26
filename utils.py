# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 15:52:37 2023

@author: Abdullah
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func
# from tzlocal import get_localzone
from app import app
from extensions import db, scheduler, cache
from models import PassData, Satellite, Reports
from intervaltree import Interval, IntervalTree
from sdrangel_requests import *
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
        for i in range(746,758):
            try:
                print(i)
                d = PassData.query.get_or_404(i)
                db.session.delete(d)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Commit Failed. Error: {e}")
   
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


Impath = 'C:/Users/Abdullah/Desktop/NOAA-Images/'
dpath = 'C:/Users/Abdullah/Desktop/NOAA-wav/'
Impath = "C:/Users/DELL/Documents/NOAA-Images/"

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
        a = Satellite.query.filter_by(Name=p.SatetlliteName).first()
        r = Reports(id = p.id,
                    size = dfsize,
                    status = pstatus,
                    dataPath = dfile,
                    imagePath = Imfilepath,
                    TLELine1 = a.TLERow1,
                    TLELine2 = a.TLERow2)
        db.session.add(r)
        try:
            db.session.commit()
            print("Report added!")
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")


#%%
# create_report(dpath,Impath,491)
# with app.app_context():
#     r = db.get_or_404(Reports,491)
#     r.imagePath = "C:/Users/DELL/Documents/NOAA-Images/apt_NOAA_19_20231003_0135.png"
#     r.status = True
#     db.session.commit()
    
# with app.app_context():
#     r = db.get_or_404(Reports,491)
#     print(r)
    
#%%

def storePassData(interval, Receive = True):
    aos = interval.begin
    los = interval.end
    el = interval.data[0]
    sat_name = interval.data[1]
    twomins = timedelta(minutes=2)
    data = PassData.query.filter(and_(PassData.AOS <= aos+twomins,
                                      PassData.AOS >= aos-twomins,
                                      PassData.SatetlliteName == sat_name)).all()
    print(data)
    if data and data[0].AOS.time() != aos.time():
        data[0].AOS = aos
    elif data and data[0].LOS.time() != los.time():
        data[0].LOS = los
    elif not data:
        p = PassData(AOS=aos,
                     LOS=los,
                     maxElevation=int(el),
                     ScheduledToReceive=Receive,
                     SatetlliteName=sat_name)
        db.session.add(p)
        db.session.flush()
        try:
            db.session.commit()
            print(f"Pass added!")
            return p
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")
        
        Onemin = timedelta(seconds=60)
        xAOS = scheduler.add_job(str(p.id)+'_AOS', AOS_macro, trigger='date',  run_date=p.AOS-Onemin, args=[p.id])
        xLOS = scheduler.add_job(str(p.id)+'_LOS', LOS_macro, trigger='date',  run_date=p.LOS+Onemin, args=[p.id])

def toDateTime(time):
    return datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%f%z').astimezone()

def updateDB():
    with scheduler.app.app_context():
        Satellites = Satellite.query.all()
        data = {}
        for sat in Satellites:
            sat_name = sat.Name
            print(sat_name)
            location = cache.get("location")
            print(f'location is {location}')
            passes = get_satellite_passes(sat_name, location)
            for p in passes:
                p['aos'] = toDateTime(p['aos'])
                p['los'] = toDateTime(p['los'])
                
            data[sat_name] = passes
        
        intervals = [Interval(i['aos'],i['los'],(i['maxElevation'],sat_name))\
                     for sat_name in data.keys() for i in data[sat_name]]
            
        tree = IntervalTree(intervals)
        
        for interval in intervals:
            tree.discard(interval)
            if tree.overlaps(interval):
                a = tree.overlap(interval)
                a = a.pop()
                tree.remove(a)
                if a.data[0] > interval.data[0]:
                    storePassData(a, True)
                    storePassData(interval, False)
                else:
                    storePassData(a, False)
                    storePassData(interval, True)
            else:
                storePassData(interval, True)

# updateDB()
#%%

def run_httpServer():
    import subprocess
    # server_path = "C:\Users\DELL\Documents\sdrangelspectrum\sdrangelspectrum\dist\sdrangelspectrum"
    p = subprocess.Popen([http-server], cwd=server_path)
    p.wait()


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
import requests
def get_tle(NORAD_ID):
    # url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={str(NORAD_ID).strip()}"
    url = cache.get("TLESource").format(str(NORAD_ID).strip())
    payload = {}
    headers = {}
    try:        
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        a = response.text
        a = [i.strip() for i in a.split("\r\n",2)]
        with open(a[0]+'.txt', 'w') as f:
            f.writelines(response.text)
        return a
    except Exception as e:
        raise e

# a = get_tle(25338)
#%%

# subprocess.Popen(sdrangel_path)
# time.sleep(30)

def launch_apps_to_virtual_desktops(desktops=2):
    import ctypes, time, shlex, subprocess
    sdrangel_path = "C:\Program Files\SDRangel\sdrangel.exe"
    virtual_desktop_accessor = ctypes.WinDLL("C:/Users/Abdullah/Desktop/NOAA/VirtualDesktopAccessor.dll")
    virtual_desktop_accessor.GoToDesktopNumber(1)
    time.sleep(0.25) # Wait for the desktop to switch
    subprocess.Popen(sdrangel_path)
    time.sleep(15) # Wait for the desktop to switch
    virtual_desktop_accessor.GoToDesktopNumber(0) # Go back to the 1st desktop
    # time.sleep(0.25) # Wait for the desktop to switch
    time.sleep(30) # Wait for apps to open their windows
    

#%%
def launch_sdr():
    if get_instance()['status'] == 'OK':
       pass
    else:
    #     subprocess.Popen(sdrangel_path)
    #     time.sleep(30)
        STR_CMD = """
        $action = New-ScheduledTaskAction -Execute "C:\Program Files\SDRangel\sdrangel.exe"
        $description = "Using PowerShell's Scheduled Tasks in Python"
        $settings = New-ScheduledTaskSettingsSet -DeleteExpiredTaskAfter (New-TimeSpan -Seconds 2)
        $taskName = "sdr"
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(10)
        $trigger.EndBoundary = (Get-Date).AddSeconds(30).ToString("s")
        Register-ScheduledTask -TaskName $taskName -Description $description -Action $action -Settings $settings -Trigger $trigger -AsJob | Out-Null
        """
        # Use a list to make it easier to pass argument to subprocess
        listProcess = [
            "powershell.exe",
            "-NoExit",
            "-NoProfile",
            "-Command",
            STR_CMD
        ]
        path = os.getcwd()
        a = subprocess.Popen(listProcess, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(25)
        b = subprocess.Popen(['powershell.exe', os.path.join(path,"hide.ps1")],cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outs, errs = b.communicate()

#%%

import subprocess
import os
from app import app, db
from models import PassData, Satellite
pk = 1327
with app.app_context():
    p = db.get_or_404(PassData,pk)
    SatelliteName = p.SatetlliteName
    aos = p.AOS
    los = p.LOS
    a = Satellite.query.filter_by(Name=SatelliteName).first()
    tle1 = a.TLERow1
    tle2 = a.TLERow2

#python fire_on_aos.py -p 1440 -s 'NOAA 18' -a '2024-01-13 6:33:45.125351' -l '2024-01-13 6:43:45.125351' -t1 '1 25338U 98030A   24009.94849596  .00000237  00000+0  11646-3 0  9992' -t2 '2 25338  98.5865  40.2731 0011332  72.3051 287.9365 14.26468234334481'
# a = subprocess.Popen(['python', 'fire_on_aos.py', '-p', str(pk), '-s', SatelliteName, '-a', aos.isoformat() , '-l', los.isoformat(), '-t1', tle1, '-t2', tle2], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
outs, errs = a.communicate()
print(outs)
print("error=",errs)
# %%