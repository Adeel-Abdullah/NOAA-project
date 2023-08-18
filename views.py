from flask import render_template, jsonify, request, Response
from models import Satellite, PassData
from app import app, db
from sdrangel_requests import *
from datetime import datetime, timedelta
from sqlalchemy import and_,func
# from test import convertodict
from jinja2  import TemplateNotFound

per_page = 10


# @app.route("/")
# def index():
#     return render_template("dashboard.html", SDRstatus = get_instance()['status'], RTLstatus=check_rtlstatus())
# SDRstatus=get_instance()['appname'], RTLstatus = check_rtlstatus())
# @app.route('/', defaults={'path': 'index.html'})
# @app.route('/')
# def index():
#   try:
#     # return render_template( 'pages/index.html', segment='index', parent='pages')
#     return render_template('pages/dashboard/dashboard.html', 
#                            segment='index')

#   except TemplateNotFound:
#     return render_template('pages/index.html'), 404
  
#   def index():
#     return render_template('home/dashboard.html', 
#                            segment='index', 
#                            user_id=current_user.id)
  
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

@app.route('/pages/settings/')
def pages_settings():
  return render_template('pages/settings.html', segment='settings', parent='pages')

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

@app.route("/ScheduledPasses")
def CountdownTimer():
    data = PassData.query.filter(and_(PassData.AOS >= datetime.now(), 
                                          PassData.ScheduledToReceive),
                                         PassData.AOS<=datetime.now()+timedelta(hours=72)).all()
    data = [d.asDict() for d in data]    
    
    return jsonify(data)

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


# if __name__ == '__main__':
#     # APP.run(host='0.0.0.0', port=5000, debug=True)
#     APP.run(debug=True)