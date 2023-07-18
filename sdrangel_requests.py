import requests
import json
import subprocess
import pytz


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

def get_satellite_passes(satelliteName):
    file_path = "./json/satellitetracker_target.json"
    with open(file_path, 'r') as openfile:
        json_object = json.load(openfile)
    json_object['SatelliteTrackerSettings']['target'] = satelliteName    
    headers = {
        'Content-Type': 'application/json'
        }
    url = "http://127.0.0.1:8091/sdrangel/featureset/feature/0/settings"
    response = requests.request("PATCH", url, headers=headers, json=json_object)
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
    
    
# result = {
#     x['aos']: datetime.strptime(x['aos'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%d-%m-%y %H:%M:%S'),
#     x['los']: datetime.strptime(x['los'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%d-%m-%y %H:%M:%S'),
#     x['maxElevation']:x['maxElevation']
#     for x in data
# }
# json.dump()