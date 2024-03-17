from flask import render_template, jsonify, request, send_file, redirect, url_for, flash
from models import Satellite, PassData, Reports, User
from app import app
from app import db, scheduler, cache, bcrypt
from sdrangel_requests import *
from scheduled_functions import AOS_macro, LOS_macro, launch_sdr, kill_sdr
from datetime import datetime, timedelta
from sqlalchemy import and_
from jinja2  import TemplateNotFound
from forms import SettingsForm, RegistrationForm, LoginForm
from flask_login import login_user, current_user, logout_user, login_required

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

@app.route('/accounts/sign-up/', methods=['GET', 'POST'])
def accounts_sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('accounts_sign_in'))
    return render_template('accounts/sign-up.html', title='Register', form=form, segment='sign_up', parent='accounts')

#   form = RegistrationForm()
#   return render_template('accounts/sign-up.html', form=form, segment='sign_up', parent='accounts')

@app.route('/accounts/login/', methods=['GET', 'POST'])
def accounts_sign_in():
    if current_user.is_authenticated:
        return redirect(url_for('pages_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('pages_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('accounts/sign-in.html', title='Login', form=form, segment='sign_in', parent='accounts')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('accounts_sign_in'))

#   form = LoginForm()
#   return render_template('accounts/sign-in.html', form=form, segment='sign_in', parent='accounts')

@app.route('/dashboard.html')
@app.route('/', defaults={'path': 'index.html'})
@app.route('/')
@login_required
def pages_dashboard():
    try:
        return render_template('pages/dashboard/dashboard.html', segment='dashboard', parent='pages')
    except TemplateNotFound:
        return render_template('pages/index.html'), 404

@app.route('/pages/tables/bootstrap-tables/')
@login_required
def pages_tables_bootstrap_tables():
  return render_template('pages/tables/bootstrap-tables.html', segment='bootstrap_tables', parent='tables')

def getSettings():
    Settings={}
    Settings['GStationName'] = cache.get('GStationName')
    Settings['latitude'] = cache.get('latitude')
    Settings['longitude'] = cache.get('longitude')
    Settings['altitude'] = cache.get('altitude')
    Settings['minElevation'] = cache.get('minElevation')
    Settings['Timezone'] = cache.get('Timezone')
    Settings['TLESource'] = cache.get('TLESource')
    Settings['AudioDirectory'] = cache.get('AudioDirectory')
    Settings['ImageDirectory'] = cache.get('ImageDirectory')
    return Settings


@app.route('/pages/settings/', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
@login_required
def pages_settings():
    settings = getSettings()
    form = SettingsForm(obj=settings)
    toggle1 = cache.get("user-notification-1")
    toggle2 = cache.get("user-notification-2")
    return render_template('pages/settings.html', segment='settings', parent='pages', form= form, S1= toggle1, S2 = toggle2, settings=settings)

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
@login_required
def page_schedule(page):
    # data = str(data.decode())
    segment = get_segment(request)
    page = page
    data = PassData.query.filter(PassData.AOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    return render_template('pages/schedule.html',  passdata = data, segment=segment, parent='pages')


@app.route('/table', methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/table/<int:page>", methods=['POST'])
@login_required
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
@login_required
def page_report(page):
    # data = str(data.decode())
    segment = get_segment(request)
    page = page
    data = (Reports.query.join(PassData).filter(PassData.LOS <= datetime.now()))\
    .order_by(PassData.AOS.desc()).paginate(page=page,per_page=per_page,error_out=False)
    return render_template('pages/received-passes-table.html',  reportdata = data, segment=segment, parent='pages')


@app.route('/<template>')
@login_required
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
@login_required
def popNOAA15(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 15"),
        PassData.LOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())


@app.route("/NOAA18", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA18/<int:page>", methods=['GET', 'POST'])
@login_required
def popNOAA18(page):
    page = page
    data = PassData.query.filter(
        and_(PassData.SatetlliteName == "NOAA 18"),
        PassData.LOS >= datetime.now()).paginate(page=page,per_page=per_page,error_out=False)
    # data = parse_table(data)
    return render_template('passestable.html', passdata = data, SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())


@app.route("/NOAA19", methods=['GET', 'POST'], defaults={"page": 1})
@app.route("/NOAA19/<int:page>", methods=['GET', 'POST'])
@login_required
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

@app.route("/getUser")
def get_user():
    if current_user.is_authenticated:
        user = current_user._get_current_object()
        return jsonify({"email":user.email})
    else:
        return jsonify("Unauthorized!"), 400


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

@app.route("/overlayMap/<int:pk>")
def overlay_map(pk):
    import subprocess
    import os
    noaaApt_path = "C:\\Users\\DELL\\Documents\\noaa-apt-1.4.1-x86_64-windows-gnu"
    p = db.get_or_404(Reports, pk)
    SatelliteName = p.PassData.SatetlliteName
    aos = p.PassData.AOS.astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')
    aos = '{0}:{1}'.format(aos[:-2], aos[-2:])
    dataPath = p.dataPath
    tle1 = p.TLELine1
    tle2 = p.TLELine2
    print(p, SatelliteName, aos, dataPath, tle1, tle2)
    a = subprocess.Popen([os.path.join(noaaApt_path,"map_overlay.bat"),dataPath, SatelliteName, aos, tle1, tle2], cwd=noaaApt_path)
    try:
        a.wait(timeout=30)
        return jsonify("success")
    except Exception as e:
        return jsonify("Error!", 500)


@app.route('/launchsdr')
def launchsdr():
    launch_sdr()
    return jsonify(message="launched successfully!")

@app.route('/killsdr')
def killsdr():
    kill_sdr()
    return jsonify(message="stopped successfully!")