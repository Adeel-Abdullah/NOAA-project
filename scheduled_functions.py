from models import Satellite, PassData, Reports
from extensions import scheduler, db, cache
import subprocess
import requests
from sdrangel_requests import *
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from intervaltree import Interval, IntervalTree


# %% adding new passes only after checking that they are not already present

def storePassData(interval, Receive = True):
    Onemin = timedelta(seconds=60)
    aos = interval.begin + Onemin
    los = interval.end - Onemin
    el = interval.data[0]
    sat_name = interval.data[1]
    twomins = timedelta(minutes=2)
    data = PassData.query.filter(and_(PassData.AOS <= aos+twomins,
                                      PassData.AOS >= aos-twomins,
                                      PassData.SatetlliteName == sat_name)).all()
    print(data)
    minEL = cache.get("minEL")
    el = int(el)
    if el < minEL:
        Receive = False
    if data and data[0].AOS.time() != aos.time():
        data[0].AOS = aos
    elif data and data[0].LOS.time() != los.time():
        data[0].LOS = los
    elif not data:
        p = PassData(AOS=aos,
                     LOS=los,
                     maxElevation=el,
                     ScheduledToReceive=Receive,
                     SatetlliteName=sat_name)
        db.session.add(p)
        db.session.flush()
        try:
            db.session.commit()
            print(f"Pass added!")
            # return p
        except Exception as e:
            db.session.rollback()
            print(f"Commit Failed. Error: {e}")
        
        Onemin = timedelta(seconds=60)
        if Receive and el >= minEL:
            xAOS = scheduler.add_job(str(p.id)+'_AOS', AOS_macro, trigger='date',  run_date=p.AOS-Onemin, args=[p.id])
            xLOS = scheduler.add_job(str(p.id)+'_LOS', LOS_macro, trigger='date',  run_date=p.LOS+Onemin, args=[p.id])

def toDateTime(time):
    return datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%f%z').astimezone()

@scheduler.task(trigger='cron', id='updateDB', hour='1,13')
def updateDB():
    if get_instance()['status'] == 'OK':
        pass
    else:
        subprocess.Popen(sdrangel_path)
        time.sleep(30)
    start_satellitetracker()
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
        Onemin = timedelta(seconds=60)
        intervals = [Interval(i['aos']-Onemin,i['los']+Onemin,(i['maxElevation'],sat_name))\
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


@scheduler.task(trigger='cron', id='updateTLE', hour='1,13')
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
    try:
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
    except Exception as e:
            print(f"Commit Failed. Error: {e}")
            
    create_report(dpath, Impath, pk)
    
    # stop_satellitetracker()
    