from flask import render_template, jsonify
from models import Satellite, PassData
from app import app
from sdrangel_requests import *
from datetime import datetime
from sqlalchemy import and_,func
from tzlocal import get_localzone

@app.route("/")
def index():
    return render_template("dashboard.html", SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())
# SDRstatus=get_instance()['appname'], RTLstatus = check_rtlstatus())

@app.route("/NOAA15", methods=['GET', 'POST'])
def popNOAA15():
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 15"),
        func.date(PassData.AOS) >= datetime.today().date()).all()
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/NOAA18", methods=['GET', 'POST'])
def popNOAA18():
    data = PassData.query.filter(
    and_(PassData.SatetlliteName == "NOAA 18"),
    func.date(PassData.AOS) >= datetime.today().date()).all()
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/NOAA19", methods=['GET', 'POST'])
def popNOAA19():
    data = data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 19"),
        func.date(PassData.AOS) >= datetime.today().date()).all()
    # data = parse_table(data)
    # SDRstatus = 
    return render_template('passestable.html', passdata = data,SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())

@app.route("/statusRTL")
def RTLstatus():
    RTLstatus = check_rtlstatus()
    return jsonify(RTLstatus = RTLstatus)

@app.route("/statusSDR")
def SDRstatus():
    SDRstatus = get_instance()['status']
    return jsonify(SDRstatus=SDRstatus)




def parse_table(data):
    return [{k:(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(get_localzone()).strftime('%d-%m-%y %H:%M:%S')
                if isinstance(v,str) else int(v)) for k,v in i.items()} for i in data]

# if __name__ == '__main__':
#     # APP.run(host='0.0.0.0', port=5000, debug=True)
#     APP.run(debug=True)