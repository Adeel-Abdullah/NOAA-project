from models import Satellite, PassData, Reports
from extensions import scheduler, db, cache
import subprocess, requests, os, time
from sdrangel_requests import *
from datetime import datetime, timedelta
from sqlalchemy import and_
from intervaltree import Interval, IntervalTree
from fire_on_aos import fire_on_aos, fire_on_los


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
    launch_sdr()
    start_satellitetracker()
    with scheduler.app.app_context():
        Satellites = Satellite.query.all()
        data = {}
        for sat in Satellites:
            sat_name = sat.Name
            print(sat_name)
            location = cache.get("location")
            print(f'location is {location}')
            alt = cache.get("altitude")
            if alt:
                passes = get_satellite_passes(sat_name, location, alt)
            else:
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
    # url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={str(NORAD_ID).strip()}"
    url = cache.get("TLESource").format(int(str(NORAD_ID).strip()))
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
            sat.TLEUpdateTime = datetime.now()
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


def create_report(dpath, default_dir, pk, Impath=None):
    import shutil, os, pathlib

    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        Imfile = getmfile(default_dir, pk)
        Imfilename = os.path.split(Imfile)[1]
        if Impath:
            shutil.move(Imfile,Impath)
            Imfile = os.path.join(Impath, Imfilename)
        dfile = getmfile(dpath,pk)
        twomins = timedelta(seconds=120)
        dmtime = datetime.fromtimestamp(dfile.stat().st_mtime)
        Imtime = datetime.fromtimestamp(pathlib.Path(Imfile).stat().st_mtime)
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
            Imfilepath = Imfile
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

def start_SpectrumServer():
    import subprocess
    import time

    server_path = "C:\\Users\\DELL\\Documents\\sdrangelspectrum\\sdrangelspectrum\\dist\\sdrangelspectrum\\"
    p = subprocess.Popen(["http-server"], stdout=subprocess.DEVNULL, cwd=server_path, shell=True, close_fds=True)
    time.sleep(1)
    print(f"Spectrum server started with ID {p.pid}!")
    return p.pid

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
        Start-ScheduledTask -TaskName "sdr"
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
        print("outs=",outs)
        print("errs=",errs)

def kill_sdr():
    pid = get_instance()['pid']
    p = psutil.Process(pid)
    p.kill()
    

def AOS_macro(pk):
    launch_sdr()
    with scheduler.app.app_context():
        p = db.get_or_404(PassData, pk)
        SatelliteName = p.SatetlliteName
        aos = p.AOS
        los = p.LOS
        sat = Satellite.query.filter_by(Name=SatelliteName).first()
        tle1 = sat.TLERow1
        tle2 = sat.TLERow2
    start_satellitetracker()
    start_rotator()
    set_preset(SatelliteName)
    start_audioRecording(SatelliteName)
    # enable_lowSampleRate()
    start_SpectrumBroadcast()
    spectrum_pid = start_SpectrumServer()
    cache.set('spectrum_pid', spectrum_pid)
    fire_on_aos(SatelliteName, str(pk), tle1, tle2, aos.isoformat(), los.isoformat())
        
    
def LOS_macro(pk):
    default_dir = "C:/Users/DELL/Documents/NOAA-Images/"
    try:
        with scheduler.app.app_context():
            p = db.get_or_404(PassData, pk)
            SatelliteName = p.SatetlliteName
        path = cache.get("AudioDirectory")
        if path:
            dpath = path
        else:
            dpath = "D:/NOAA-wav/"

        Impath = cache.get("ImageDirectory")                              
        stop_audioRecording(SatelliteName)
        stop_rotator()
        stop_SpectrumBroadcast()
        pid = get_instance()['pid']
        p = psutil.Process(pid)
        p.kill()
        spectrum_pid = cache.get('spectrum_pid')
        p = psutil.Process(spectrum_pid)
        p.kill()
    except Exception as e:
            print(f"Commit Failed. Error: {e}")
            
    create_report(dpath, default_dir, pk, Impath)
    fire_on_los(str(pk))
    # stop_satellitetracker()
