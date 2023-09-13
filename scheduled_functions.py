from models import Satellite, PassData
from extensions import scheduler, db
import requests
from sdrangel_requests import *
from datetime import datetime, timedelta
from sqlalchemy import and_, func


# %% adding new passes only after checking that they are not already present

@scheduler.task(trigger='cron', id='updateDB', minute='*/5')
def updateDB():
    with scheduler.app.app_context():
        Satellites = Satellite.query.all()
        for sat in Satellites:
            sat_name = sat.Name
            print(sat_name)
            passes = get_satellite_passes(sat_name)
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



@scheduler.task(trigger='interval', id='updateTLE', minutes=2)
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