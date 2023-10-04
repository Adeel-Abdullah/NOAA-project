from models import Satellite, PassData, Reports
from extensions import scheduler, db, cache
import subprocess
import requests
from sdrangel_requests import *
from datetime import datetime, timedelta
from sqlalchemy import and_, func


# %% adding new passes only after checking that they are not already present

@scheduler.task(trigger='cron', id='updateDB', hour='*/4')
def updateDB():
    if get_instance()['status'] == 'OK':
        pass
    else:
        subprocess.Popen(sdrangel_path)
        time.sleep(15)
    start_satellitetracker()
    with scheduler.app.app_context():
        Satellites = Satellite.query.all()
        for sat in Satellites:
            sat_name = sat.Name
            print(sat_name)
            location = cache.get("location")
            passes = get_satellite_passes(sat_name, location)
            twomins = timedelta(minutes=2)
            for p in passes:
                aos = datetime.strptime(
                    p['aos'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                los = datetime.strptime(
                    p['los'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
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
                                   maxElevation=int(p['maxElevation']),
                                   SatetlliteName=sat_name)
                    db.session.add(p)
                    db.session.flush()
                    try:
                        db.session.commit()
                        print(f"Pass added!")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Commit Failed. Error: {e}")
                        
                    Onemin = timedelta(seconds=60)
                    xAOS = scheduler.add_job(str(p.id)+'_AOS', AOS_macro, trigger='date',  run_date=p.AOS-Onemin, args=[p.id])
                    xLOS = scheduler.add_job(str(p.id)+'_LOS', LOS_macro, trigger='date',  run_date=p.LOS+Onemin, args=[p.id])
                    


# %% update satellite tle

def get_tle(NORAD_ID):
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR={}".format(str(NORAD_ID).strip())
    payload = {}
    headers = {}
    try:        
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        a = response.text
        a = [i.strip() for i in a.split("\r\n",2)]
        return a
    except Exception as e:
        raise e



@scheduler.task(trigger='cron', id='updateTLE', hour='*/8')
def update_tle():
    with scheduler.app.app_context():
        Satellites = Satellite.query.all()
        for sat in Satellites:
            Nor_id = sat.Norad_id
            try:
                t = get_tle(Nor_id)
            except Exception as e:
                print(f"TLE not fetched! Error: {e}")
                return
            sat.TLERow1 = t[1]
            print(sat.TLERow1)
            sat.TLERow2 = t[2]
            print(sat.TLERow2)
            try:
                db.session.commit()
                print(f"TLE added!")
            except Exception as e:
                db.session.rollback()
                print(f"Commit Failed. Error: {e}")

def getmfile(search_dir, pk):
    import os
    
    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        time = p.LOS## - timedelta(hours=3) ## The timedelta is added for timzone correction!
    files = list(os.scandir(search_dir))
    
    # return files
    files = sorted(files,reverse = True, key=lambda x:(datetime.fromtimestamp(x.stat().st_mtime)))
    print(datetime.fromtimestamp(files[0].stat().st_mtime).isoformat())
    print(files[0])
    return files[0]


def create_report(dpath, Impath, pk):
    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        Imfile = getmfile(Impath, pk)
        dfile = getmfile(dpath,pk)
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


def AOS_macro(pk):
    if get_instance()['status'] == 'OK':
       pass
    else:
        subprocess.Popen(sdrangel_path)
        time.sleep(30)

    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        SatelliteName = p.SatetlliteName
    start_satellitetracker()
    start_rotator()
    set_preset(SatelliteName)
    start_audioRecording(SatelliteName)
        
    
def LOS_macro(pk):
    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        SatelliteName = p.SatetlliteName
    dpath = "D:/NOAA-wav/"
    Impath = "C:/Users/DELL/Documents/NOAA-Images/"
    
    stop_audioRecording(SatelliteName)
    stop_rotator()
    pid = get_instance()['pid']
    p = psutil.Process(pid)
    p.kill()
    create_report(dpath, Impath, pk)
    
    # stop_satellitetracker()
    