from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, IntegerField, DecimalField
from wtforms.validators import Length, ValidationError, optional
import datetime

def ValidateDirectory(form, field):
        from pathlib import Path
        if field.data is not None and not Path(field.data).exists() :
            raise ValidationError("invalid directory!")

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

        
    
