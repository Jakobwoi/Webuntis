#!/usr/bin/env python
import asyncio
import datetime
import json
import requests
import pyotp
import Python.login_config as login_config

# Configuration
KEY = login_config.KEY  # Key used to generate the OTP
SCHOOL = login_config.SCHOOL        # WebUntis school name
USERNAME = login_config.USERNAME # WebUntis username
SERVER_URL = login_config.SERVER_URL  # WebUntis server URL

async def get_otp_token():
    """Generate the OTP token using pyotp."""
    totp = pyotp.TOTP(KEY, interval=30)
    return totp.now()

async def login(scname, server, token, username, time):
    """Login to WebUntis using OTP and get session cookie."""
    url = f"{server}/WebUntis/jsonrpc_intern.do"
    headers = {'Content-Type': 'application/json'}
    print(type(headers))
    data = {
        'id': 'Awesome',
        'method': 'getUserData2017',
        'params': [
            {
                'auth': {
                    'clientTime': time,
                    'user': username,
                    'otp': token,
                },
            },
        ],
        'jsonrpc': '2.0',
    }
    params = {
        'm': 'getUserData2025',
        'school': scname,
        'v': 'i2.2',
    }
    
    response = requests.post(url, json=data, headers=headers, params=params)
    
    if 'set-cookie' in response.headers:
        cookie_parts = response.headers['set-cookie'].split('; ')
        jsessionid = None
        for part in cookie_parts:
            if part.startswith('JSESSIONID='):
                jsessionid = part[len('JSESSIONID='):]
                break
                
        if jsessionid:
            return jsessionid
    
    raise Exception("Failed to login: No session cookie found")

async def get_timetable(jsessionid, start_date, end_date, element_type, element_id):
    """
    Fetch timetable data using JSON-RPC API.
    
    element_type values:
    - 1 = klasse (class)
    - 2 = teacher
    - 3 = subject
    - 4 = room
    - 5 = student
    """
    url = f"{SERVER_URL}/WebUntis/jsonrpc.do"
    
    # Convert datetime to WebUntis format (YYYYMMDD)
    start_formatted = start_date.strftime("%Y%m%d")
    end_formatted = end_date.strftime("%Y%m%d")
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'JSESSIONID={jsessionid}'
    }
    
    data = {
        'id': 'get_timetable',
        'method': 'getTimetable',
        'params': {
            'options': {
                'element': {
                    'id': element_id,
                    'type': element_type
                },
                'startDate': start_formatted,
                'endDate': end_formatted,
                'showStudentgroup': True,
                'showLsText': True,
                'showLsNumber': True,
                'showInfo': True,
                'showBooking': True,
                'klasseFields': ["id", "name", "longname", "externalkey"],
                'roomFields': ["id", "name", "longname", "externalkey"],
                'subjectFields': ["id", "name", "longname", "externalkey"],
                'teacherFields': ["id", "name", "longname", "externalkey"]
            }
        },
        'jsonrpc': '2.0'
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

async def get_classes(jsessionid):
    """Fetch all classes (Klassen) data."""
    url = f"{SERVER_URL}/WebUntis/jsonrpc.do"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'JSESSIONID={jsessionid}'
    }
    
    data = {
        'id': 'get_classes',
        'method': 'getKlassen',
        'params': {},
        'jsonrpc': '2.0'
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

async def get_classes(jsessionid):
    """Fetch all classes (Klassen) data."""
    url = f"{SERVER_URL}/WebUntis/jsonrpc.do"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'JSESSIONID={jsessionid}'
    }
    
    data = {
        'id': 'get_classes',
        'method': 'getKlassen',
        'params': {},
        'jsonrpc': '2.0'
    }
    
    response = requests.get(url, json=data, headers=headers)
    return response

async def main():
    try:
        # Generate OTP token
        token = await get_otp_token()
        
        # Get current timestamp in milliseconds
        current_time = int(datetime.datetime.now().timestamp() * 1000)
        
        # Login to WebUntis
        print("Logging in to WebUntis...")
        jsessionid = await login(SCHOOL, SERVER_URL, token, USERNAME, current_time)
        print(f"Login successful. Session ID: {jsessionid}")
        
        # Get all classes
        classes_data = await get_classes(jsessionid)
        print("Classes data retrieved.")
        
        # Find class with name '6d'
        klasse_id = None
        for klasse in classes_data.get('result', []):
            if klasse.get('name') == '6d':
                klasse_id = klasse.get('id')
                print(f"Found class 6d with ID: {klasse_id}")
                break
        
        if not klasse_id:
            print("Class '6d' not found!")
            return
        
        # Get timetable for today
        today = datetime.date.today()
        
        # Get timetable for class 6d
        print("Fetching timetable...")
        timetable_data = await get_timetable(
            jsessionid,
            today,  # start date
            today,  # end date
            1,      # element type 1 = class
            klasse_id
        )
        
        # Save the timetable to a JSON file
        with open('timetable.json', 'w', encoding='utf-8') as f:
            json.dump(timetable_data, f, ensure_ascii=False, indent=2)
        
        print("Timetable saved to timetable.json")
        
        # Example: Print some basic info from the timetable
        if 'result' in timetable_data:
            periods = timetable_data['result']
            print(f"Retrieved {len(periods)} periods for today.")
            
            # Print summary of each period
            for period in periods:
                start_time = period.get('startTime', 0)
                end_time = period.get('endTime', 0)
                
                # Format times from HHMM to HH:MM
                start_str = f"{start_time//100:02d}:{start_time%100:02d}"
                end_str = f"{end_time//100:02d}:{end_time%100:02d}"
                
                subjects = [s.get('name', 'Unknown') for s in period.get('su', [])]
                teachers = [t.get('name', 'Unknown') for t in period.get('te', [])]
                rooms = [r.get('name', 'Unknown') for r in period.get('ro', [])]
                
                print(f"{start_str}-{end_str}: {', '.join(subjects)} | {', '.join(teachers)} | {', '.join(rooms)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
