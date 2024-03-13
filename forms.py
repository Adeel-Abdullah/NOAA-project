from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, IntegerField, DecimalField, PasswordField, SubmitField
from wtforms.validators import Length, ValidationError, optional, DataRequired, Email, EqualTo
import datetime
from models import User

def ValidateDirectory(form, field):
        from pathlib import Path
        if field.data is not None and not Path(field.data).exists() :
            # raise ValidationError("invalid directory!")
            raise ValidationError("无效的目录！")

class SettingsForm(FlaskForm):
    GStationName = StringField("Ground Station Name", validators=[Length(max=20)], render_kw={"placeholder": "Earth Station"})
    latitude = DecimalField("Latitude", places=6, description='Latitude', render_kw={"placeholder": "Latitude"}, validators=[optional()])
    longitude = DecimalField("Longitude", places=6, description='Longitude', render_kw={"placeholder": "Longitude"}, validators=[optional()])
    altitude = IntegerField("Altitude", description="From Mean Sea Level", render_kw={"placeholder": "From Mean Sea Level"}, validators=[optional()])
    minElevation = IntegerField("Minimum Elevation", description="Minimum Elevation Pass to Recieve", render_kw={"placeholder": "Minimum Elevation to Receive"}, validators=[optional()])
    Timezone = SelectField("Timezone", description="Default Timezone", choices=[(datetime.datetime.now().astimezone().tzinfo, 'Local Time'),
                                                                                (datetime.timezone.utc,'UTC')],
                                                                                render_kw={"placeholder": "Default Timezone"})
    TLESource = SelectField("TLE Source", description="Default TLE Source", 
                            choices=[("https://celestrak.org/NORAD/elements/gp.php?CATNR={:d}","celestrak"),
                                     ("https://db.satnogs.org/api/tle/?format=3le&norad_cat_id={:d}","satnogs") ],
                                     render_kw={"placeholder": "Default TLE Source"})
    
    AudioDirectory = StringField("Wav File Directory", description="D:/NOAA-wav", validators=[ValidateDirectory],
                                 render_kw={"placeholder": r"D:\NOAA-wav"})
    ImageDirectory = StringField("Product Directory", description="C:/Users/DELL/Documents/NOAA-Images", validators=[ValidateDirectory],
                                 render_kw={"placeholder": r"C:\Users\DELL\Documents\NOAA-Images"})
    ###

    GStationName = StringField("地面站名称", validators=[Length(max=20)], render_kw={"placeholder": "地球站"})
    latitude = DecimalField("纬度", places=6, description='纬度', render_kw={"placeholder": "纬度"}, validators=[optional()])
    longitude = DecimalField("经度", places=6, description='经度', render_kw={"placeholder": "经度"}, validators=[optional()])
    altitude = IntegerField("海拔", description="从平均海平面出发", render_kw={"placeholder": "从平均海平面出发"}, validators=[optional()])
    minElevation = IntegerField("最小仰角", description="接收的最低海拔通行证", render_kw={"placeholder": "接收的最低海拔通行证"}, validators=[optional()])
    Timezone = SelectField("时区", description="默认时区", choices=[(datetime.datetime.now().astimezone().tzinfo, '本地时间'),
                                                                                (datetime.timezone.utc,'UTC')],
                                                                                render_kw={"placeholder": "默认时区"})
    TLESource = SelectField("轨道数据", description="默认 TLE 源", 
                            choices=[("https://celestrak.org/NORAD/elements/gp.php?CATNR={:d}","celestrak"),
                                     ("https://db.satnogs.org/api/tle/?format=3le&norad_cat_id={:d}","satnogs") ],
                                     render_kw={"placeholder": "默认 TLE 源"})
    
    AudioDirectory = StringField("原始数据地址", description="D:/NOAA-wav", validators=[ValidateDirectory],
                                 render_kw={"placeholder": r"D:\NOAA-wav"})
    ImageDirectory = StringField("卫星图像地址", description="C:/Users/DELL/Documents/NOAA-Images", validators=[ValidateDirectory],
                                 render_kw={"placeholder": r"C:\Users\DELL\Documents\NOAA-Images"})

        
class RegistrationForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()],
                        render_kw={"placeholder":"example@company.com"})
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    TnC = BooleanField('Terms and Conditions')
    submit = SubmitField('Sign Up')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
        

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()],
                        render_kw={"placeholder":"example@company.com"})
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

