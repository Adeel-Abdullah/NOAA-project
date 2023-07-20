from flask import render_template, jsonify, request
from models import Satellite, PassData
from app import app, db
from sdrangel_requests import *
from datetime import datetime
from sqlalchemy import and_,func
from tzlocal import get_localzone

per_page = 10


@app.route("/")
def index():
    return render_template("dashboard.html", SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())
# SDRstatus=get_instance()['appname'], RTLstatus = check_rtlstatus())

@app.route("/NOAA15", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA15/<int:page>", methods=['GET', 'POST'])
def popNOAA15(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 15"),
        PassData.AOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/NOAA18", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA18/<int:page>", methods=['GET', 'POST'])
def popNOAA18(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 18"),
        PassData.AOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/NOAA19", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA19/<int:page>", methods=['GET', 'POST'])
def popNOAA19(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 19"),
        PassData.AOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    # SDRstatus = 
    return render_template('passestable.html', passdata = data,SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/Countdown")
def CountdownTimer():
    data = PassData.query.filter(and_(PassData.AOS >= datetime.now(), 
                                         PassData.ScheduledToReceive)).first()
    return jsonify(AOS_time = data.AOS)

@app.route("/statusRTL")
def RTLstatus():
    RTLstatus = check_rtlstatus()
    return jsonify(RTLstatus = RTLstatus)

@app.route("/statusSDR")
def SDRstatus():
    SDRstatus = get_instance()['status']
    return jsonify(SDRstatus=SDRstatus)

@app.route("/schedulePasses", methods=['POST'])
def schedulePasses():
    scheduledPasses = []
    unscheduledPasses = []
    with app.app_context():
        for pk in request.json['checked']:
            d = db.get_or_404(PassData, pk)
            d.ScheduledToReceive=True
            scheduledPasses.append(d)
            db.session.commit()
            
        for pk in request.json['unchecked']:
            d = db.get_or_404(PassData, pk)
            d.ScheduledToReceive=False
            unscheduledPasses.append(d)
            db.session.commit()
    return jsonify(message="Scheduling Successful!")





def parse_table(data):
    return [{k:(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()).strftime('%d-%m-%y %H:%M:%S')
                if isinstance(v,str) else int(v)) for k,v in i.items()} for i in data]

# if __name__ == '__main__':
#     # APP.run(host='0.0.0.0', port=5000, debug=True)
#     APP.run(debug=True)