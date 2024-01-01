import requests
import json
import subprocess
import time
import psutil


sdrangel_path = "C:\Program Files\SDRangel\sdrangel.exe"


def get_instance():
    url = "http://127.0.0.1:8091/sdrangel"
    payload = {}
    headers = {}
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        data['status'] = 'OK'
    except requests.exceptions.ConnectionError as err:
        return {'pid': None, 'message': "SDRangel is inactive!", 'status': None}
                
    return(data)

def check_sdrstatus(pid):
    try:
        p = psutil.Process(pid)
        if(p.name() == 'sdrangel.exe' and p.status() == 'running'):
            return {'pid': pid, 'message': "SDRangel is active!", 'status': 'OK'}
        else:
            return get_instance()
    except Exception as e:
        p = get_instance()
        return p
        

def get_sdrangel_config():
    payload = {}
    headers = {}
    url = "http://127.0.0.1:8091/sdrangel/config"
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
    except requests.exceptions.ConnectionError as err:
        return
    return(response.json())


def set_sdrangel_config(file_path):
    url = "http://127.0.0.1:8091/sdrangel/config"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    payload = json_object
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("PATCH", url, headers=headers, json=payload)
    return(response.json())

def get_features():
    url = "http://127.0.0.1:8091/sdrangel/featureset"
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return(response.json())


def start_satellitetracker():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/run"
    payload = {}
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)
    return(response.json())


def stop_satellitetracker():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/run"
    payload = {}
    headers = {}
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return(response.json())


def start_rotator():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/1/run"
    payload = {}
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)
    return(response.json())

def stop_rotator():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/1/run"
    payload = {}
    headers = {}
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return(response.json())


def get_satellitetracker_settings():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/settings"
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return(response.json())

def get_sdrangel_passes():
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/report"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    return(response.json())

def get_satellite_passes(satelliteName, location, altitude= 0):
    file_path = "./json/satellitetracker_target.json"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    json_object['SatelliteTrackerSettings']['target'] = satelliteName
    json_object['SatelliteTrackerSettings']['heightAboveSeaLevel'] = altitude
    json_object['SatelliteTrackerSettings']['latitude'] = location['latitude']
    json_object['SatelliteTrackerSettings']['longitude'] = location['longitude']
    print(location)
    headers = {
        'Content-Type': 'application/json'
        }
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/settings"
    response = requests.request("PATCH", url, headers=headers, json=json_object)
    time.sleep(2)
    data = get_sdrangel_passes()
    for datum in data["SatelliteTrackerReport"]["satelliteState"]:
        if satelliteName in datum.values():
            return(datum["passes"])


def check_rtlstatus():
    out = subprocess.getoutput("PowerShell -Command \"& {Get-PnpDevice | Select-Object Status,Class,FriendlyName,InstanceId | ConvertTo-Json}\"")
    j = json.loads(out)
    for dev in j:
        if (dev['FriendlyName'] == 'Bulk-In, Interface' or dev['FriendlyName'] == 'RTL2832U') and dev['Class'] == 'USBDevice':
            return(dev['Status'] )
    

def get_presets():
    url = "http://127.0.0.1:8091/sdrangel/presets"
    
    payload = {}
    headers = {}
    
    response = requests.request("GET", url, headers=headers, data=payload)
    
    return(response.json())

def find_preset(json_object, Name):
    for i in json_object['groups'][0]['presets']:
        if i['name'] == Name:

            return i

def set_preset(satelliteName):
    url = "http://127.0.0.1:8091/sdrangel/preset"
    
    file_path = "json/presets.json"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    
    preset = find_preset(json_object, satelliteName)
    
    file_path = "json/preset.json"
    with open(file_path, 'r') as openfile:
        json_object = openfile.read()
    
    from string import Template
    t = Template(json_object.replace('{','${'))
    payload = t.safe_substitute(freq=preset['centerFrequency'], 
                                type=preset['type'], 
                                name=preset['name'])
    payload = payload.replace('${', '{')
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text

# set_preset("NOAA 15")


def start_audioRecording(SatelliteName):
    url = "http://127.0.0.1:8091/sdrangel/audio/output/parameters"
    file_path = "json/start_recording.json"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    
    json_object['fileRecordName'] = json_object['fileRecordName'].format(SatelliteName)
    payload = json.dumps(json_object)
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text

# start_audioRecording()

def stop_audioRecording(SatelliteName):
    url = "http://127.0.0.1:8091/sdrangel/audio/output/parameters"
    file_path = "json/stop_recording.json"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    
    json_object['fileRecordName'] = json_object['fileRecordName'].format(SatelliteName)
    payload = json.dumps(json_object)
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text

def start_SpectrumBroadcast():
    url = "http://127.0.0.1:8091/sdrangel/deviceset/0/spectrum/server"
    payload = {}
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def stop_SpectrumBroadcast():
    url = "http://127.0.0.1:8091/sdrangel/deviceset/0/spectrum/server"

    payload = {}
    headers = {}

    response = requests.request("DELETE", url, headers=headers, data=payload)

    return response.text

def enable_lowSampleRate():
    url = "http://127.0.0.1:8091/sdrangel/deviceset/0/device/settings"

    payload = "{\r\n    \"deviceHwType\": \"RTLSDR\",\r\n    \"direction\": 0,\r\n    \"rtlSdrSettings\": {\r\n        \"lowSampleRate\": 1\r\n    }\r\n}\r\n"
    headers = {
    'Content-Type': 'text/plain'
    }
    print("enabling low sample rate")
    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text

def disable_lowSampleRate():
    url = "http://127.0.0.1:8091/sdrangel/deviceset/0/device/settings"

    payload = "{\r\n    \"deviceHwType\": \"RTLSDR\",\r\n    \"direction\": 0,\r\n    \"rtlSdrSettings\": {\r\n        \"lowSampleRate\": 0\r\n    }\r\n}"
    headers = {
    'Content-Type': 'text/plain'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text



    

# result = {
#     x['aos']: datetime.strptime(x['aos'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%d-%m-%y %H:%M:%S'),
#     x['los']: datetime.strptime(x['los'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%d-%m-%y %H:%M:%S'),
#     x['maxElevation']:x['maxElevation']
#     for x in data
# }
# json.dump()