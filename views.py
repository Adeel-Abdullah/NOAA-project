from flask import render_template, jsonify, request, send_file
from models import Satellite, PassData, Reports
from app import app
from app import db, scheduler, cache
from sdrangel_requests import *
from scheduled_functions import AOS_macro, LOS_macro, launch_sdr, kill_sdr
from datetime import datetime, timedelta
from sqlalchemy import and_
from jinja2  import TemplateNotFound
from forms import SettingsForm

per_page = 10

KHI_location={
    'latitude': 24.958952,
    'longitude': 67.222534}
CS_location={
    'latitude': 28.235100,
    'longitude': 112.931328}

if not cache.get("location"):
    cache.set("location", CS_location)

if not cache.get("minEL"):
    cache.set("minEL", 15)


@app.route('/dashboard.html')
@app.route('/', defaults={'path': 'index.html'})
@app.route('/')
def pages_dashboard():
    try:
        return render_template('pages/dashboard/dashboard.html', segment='dashboard', parent='pages')
    except TemplateNotFound:
        return render_template('pages/index.html'), 404

@app.route('/pages/tables/bootstrap-tables/')
def pages_tables_bootstrap_tables():
  return render_template('pages/tables/bootstrap-tables.html', segment='bootstrap_tables', parent='tables')

@app.route('/pages/settings/', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def pages_settings():
    form = SettingsForm()
    toggle1 = cache.get("user-notification-1")
    toggle2 = cache.get("user-notification-2")
    return render_template('pages/settings.html', segment='settings', parent='pages', form= form, S1= toggle1, S2 = toggle2)

@app.route('/updateSettings', methods=['POST'])
def updateSettings():
    form = SettingsForm()
    if form.validate_on_submit():
        data = {k: v for k, v in form.data.items() if v is not None}
        print(data)
        for key, value in data.items():
            cache.set(key, value)
        return render_template('pages/errors.html', form=form), 200
    else:
        return render_template('pages/errors.html', form=form), 400


@app.route('/schedule.html', methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/schedule.html/<int:page>", methods=['GET', 'POST'])
def page_schedule(page):
    # data = str(data.decode())
    segment = get_segment(request)
    page = page
    data = PassData.query.filter(PassData.AOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    return render_template('pages/schedule.html',  passdata = data, segment=segment, parent='pages')


@app.route('/table', methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/table/<int:page>", methods=['POST'])
def table(page):
    data = request.data
    data = json.loads(data)
    segment = get_segment(request)
    page = page
    data = PassData.query.filter(and_(PassData.AOS >= datetime.now(),
                                      PassData.SatetlliteName.in_(data.values()))).paginate(page=page,per_page=per_page,error_out=False)
    return render_template('pages/tables/tables.html',  passdata = data, segment=segment, parent='pages')


@app.route('/received-passes-table.html', methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/received-passes-table.html/<int:page>", methods=['GET', 'POST'])
def page_report(page):
    # data = str(data.decode())
    segment = get_segment(request)
    page = page
    data = (Reports.query.join(PassData).filter(PassData.LOS <= datetime.now()))\
    .order_by(PassData.AOS.desc()).paginate(page=page,per_page=per_page,error_out=False)
    return render_template('pages/received-passes-table.html',  reportdata = data, segment=segment, parent='pages')


@app.route('/<template>')
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("pages/" + template, segment=segment)
    except TemplateNotFound:
        return render_template('pages/page-404.html'), 404
    except:
        return render_template('pages/page-500.html'), 500

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None


@app.route("/NOAA15", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA15/<int:page>", methods=['GET', 'POST'])
def popNOAA15(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 15"),
        PassData.LOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())


@app.route("/NOAA18", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA18/<int:page>", methods=['GET', 'POST'])
def popNOAA18(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 18"),
        PassData.LOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())


@app.route("/NOAA19", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA19/<int:page>", methods=['GET', 'POST'])
def popNOAA19(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 19"),
        PassData.LOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    # SDRstatus = 
    return render_template('passestable.html', passdata = data,SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())


@app.route("/ScheduledPasses")
def CountdownTimer():
    data = PassData.query.filter(and_(PassData.LOS >= datetime.now(), 
                                        PassData.ScheduledToReceive),
                                        PassData.AOS<=datetime.now()+timedelta(hours=72)).all()
    data = [d.asDict() for d in data]    
    
    return jsonify(data)

@app.route("/notificationStatus", methods=['POST'])
def updateNotificationStatus():
    data = request.json
    # print(data)
    # print(data['value'])
    cache.set(data['id'], data['value'])
    print(f"{data['id']} is now {data['value']}!")
    return jsonify(success=True)


@app.route("/statusRTL")
def RTLstatus():
    RTLstatus = check_rtlstatus()
    return jsonify(RTLstatus = RTLstatus)

@app.route("/statusSDR")
def SDRstatus():
    pid = cache.get('pid')
    SDRstatus = check_sdrstatus(pid)
    if SDRstatus['pid']:
        cache.set('pid', SDRstatus['pid'])
    SDRstatus = SDRstatus['status']
    return jsonify(SDRstatus=SDRstatus)

@app.route("/statusROT")
def ROTstatus():
    try:
        if cache.get('pid'):
            resp = get_rotatorStatus()
            return jsonify(resp)
        else:
            return jsonify(state = "busy")
    except Exception as e:
        return jsonify(state = "unavailable")

def schedulePass(pk):
    Onemin = timedelta(seconds=60)
    d = db.get_or_404(PassData, pk)
    d.ScheduledToReceive=True
    aos_job = scheduler.get_job(str(pk)+'_AOS')
    los_job = scheduler.get_job(str(pk)+'_LOS')
    if aos_job:
        pass
    else:
        scheduler.add_job(
            str(d.id)+'_AOS', AOS_macro, trigger='date',  run_date=d.AOS-Onemin, args=[d.id])
    if los_job:
        pass
    else:
        scheduler.add_job(
            str(d.id)+'_LOS', LOS_macro, trigger='date',  run_date=d.LOS+Onemin, args=[d.id])
    db.session.commit()

def unschedulePass(pk):
    Onemin = timedelta(seconds=60)
    d = db.get_or_404(PassData, pk)
    d.ScheduledToReceive=False
    aos_job = scheduler.get_job(str(pk)+'_AOS')
    los_job = scheduler.get_job(str(pk)+'_LOS')
    if aos_job:
        aos_job = scheduler.remove_job(str(pk)+'_AOS')
    else:
        pass
    if los_job:
        los_job = scheduler.remove_job(str(pk)+'_LOS')
    else:
        pass
    db.session.commit()


@app.route("/schedulePasses", methods=['POST'])
def schedulePasses():
    for pk in request.json['checked']:
        schedulePass(pk)
        
    for pk in request.json['unchecked']:
        unschedulePass(pk)
    return jsonify(message="Scheduling Successful!")


@app.route('/location')
def get_loc():
    if (request.args.get('latitude') and request.args.get('longitude')):
        location = {
            'latitude': request.args.get('latitude'),
            'longitude': request.args.get('longitude')
        }
        cache.set("location", location)
        resp = {"latitude":location['latitude'], "longitude":location['longitude'],
                "GStationName":cache.get("GStationName")}
        return jsonify(resp)
    else:
        resp = {"latitude":cache.get("location")['latitude'], "longitude":cache.get("location")['longitude'],
                "GStationName":cache.get("GStationName")}
        return jsonify(resp)
        # return jsonify(cache.get("location"), {"GStationName": cache.get("GStationName")})


@app.route('/setminEL/<int:minEL>')
def set_minEL(minEL):
    cache.set("minEL", minEL)
    scheduledPasses = PassData.query.filter(and_(PassData.AOS >= datetime.now(), 
                                    PassData.maxElevation >= minEL )).all()
    for p in scheduledPasses:
        schedulePass(p.id)

    unscheduledPasses = PassData.query.filter(and_(PassData.AOS >= datetime.now(), 
                                    PassData.maxElevation < minEL )).all()
    for p in unscheduledPasses:
        unschedulePass(p.id)

    return jsonify(message="Minimum Elevation Set!"), 201



@app.route("/tle/<string:name>")
def fetch_tle(name):
    import re
    # with app.app_context:
    name = str(name).lower()
    name = re.split(r'[^\w]',name)
    name = ''.join(name)
    name = re.split('(\d+)',name)
    name = '%'.join(name)
    name = f"%{name}%"
    sat = Satellite.query.filter(Satellite.Name.ilike(name)).first()
    try:
        response = jsonify(sat.Name, sat.TLERow1, sat.TLERow2, sat.TLEUpdateTime)
        return response
    except Exception as e:
        return jsonify({"message": "Not Found!"}), 404


@app.route("/fetchImage/<int:pk>")
def fetch_image(pk):
    r = db.get_or_404(Reports, pk)
    img = r.imagePath
    # img = "C:/Users/Abdullah/Desktop/NOAA-Images/apt_NOAA_18_20231002_0348.png"
    return send_file(
        img,
        download_name='image.png',
        mimetype='image/png'
    )


@app.route("/fetchData/<int:pk>")
def fetch_data(pk):
    print(pk)
    r = db.get_or_404(Reports, pk)
    path = r.dataPath
    # path = "C:/Users/Abdullah/Desktop/NOAA-wav/NOAA 18_2023-10-02T03_47_39_163.wav"
    # data = ""
    # return send_from_directory(path, data)
    return send_file(
        path,
        download_name="data.wav",
        mimetype="audio/wav"
    )

@app.route("/playAudio/<int:pk>")
def play_audio(pk):
    # path = "C:/Users/Abdullah/Desktop/NOAA-wav/NOAA 18_2023-10-02T03_47_39_163.wav"
    # data = ""
    # return send_from_directory(path, data)
    return (
        f'<body style="background-color:dark; align-items: center;  display: flex; justify-content: center;">\
        <div> \
        <audio controls="">\
        <source src="http://127.0.0.1:5000/fetchData/{pk}" type="audio/wav">\
         </audio> </div> </body>'
    )

@app.route('/launchsdr')
def launchsdr():
    launch_sdr()
    return jsonify(message="launched successfully!")

@app.route('/killsdr')
def killsdr():
    kill_sdr()
    return jsonify(message="stopped successfully!")