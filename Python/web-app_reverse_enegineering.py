#!/usr/bin/env python
import asyncio
import datetime
import json
import requests
import re
import pyotp
from collections import defaultdict
import login_config as login_config
from bs4 import BeautifulSoup

# Configuration
KEY = login_config.KEY  # Key used to generate the OTP
SCHOOL = login_config.SCHOOL        # WebUntis school name
USERNAME = login_config.USERNAME # WebUntis username
SERVER_URL = login_config.SERVER_URL  # WebUntis server URL

async def get_otp_token():
    totp = pyotp.TOTP(KEY, interval=30)
    return totp.now()

async def time_grid_number(start, end):
    """Calculate the time grid number for WebUntis API."""
    match start:
        case datetime.time(hour=8, minute=0):
            grid_number_start = 1
        case datetime.time(hour=8, minute=55):
            grid_number_start = 2
        case datetime.time(hour=9, minute=50):
            grid_number_start = 3
        case datetime.time(hour=10, minute=55):
            grid_number_start = 4
        case datetime.time(hour=11, minute=50):
            grid_number_start = 5
        case datetime.time(hour=12, minute=45):
            grid_number_start = 6
        case datetime.time(hour=13, minute=40):
            grid_number_start = 7
        case datetime.time(hour=14, minute=30):
            grid_number_start = 8
        case datetime.time(hour=15, minute=20):
            grid_number_start = 9
        case datetime.time(hour=16, minute=10):
            grid_number_start = 10
        case datetime.time(hour=17, minute=0):
            grid_number_start = 11
        case _:
            raise ValueError("Invalid start time")
    match end:
        case datetime.time(hour=8, minute=50):
            grid_number_end = 1
        case datetime.time(hour=9, minute=45):
            grid_number_end = 2
        case datetime.time(hour=10, minute=40):
            grid_number_end = 3
        case datetime.time(hour=11, minute=45):
            grid_number_end = 4
        case datetime.time(hour=12, minute=40):
            grid_number_end = 5
        case datetime.time(hour=13, minute=35):
            grid_number_end = 6
        case datetime.time(hour=14, minute=30):
            grid_number_end = 7
        case datetime.time(hour=15, minute=20):
            grid_number_end = 8
        case datetime.time(hour=16, minute=10):
            grid_number_end = 9
        case datetime.time(hour=17, minute=0):
            grid_number_end = 10
        case datetime.time(hour=17, minute=50):
            grid_number_end = 11
        case _:
            raise ValueError("Invalid end time")
    return grid_number_start, grid_number_end

async def login(scname, server, token, username, time):
    """Login to WebUntis using OTP and get session cookie."""
    url = f"{server}/WebUntis/jsonrpc_intern.do"
    headers = {'Content-Type': 'application/json'}
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
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
                }
            response = requests.get(f"{SERVER_URL}/WebUntis/api/token/new", headers=headers, cookies={'JSESSIONID': jsessionid})
            token = response.text
            return {'jsessionid': jsessionid,
                    'token': token}
    
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

async def get_holidays(jsessionid):
    """Fetch all holidays data."""
    url = f"{SERVER_URL}/WebUntis/jsonrpc.do"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'JSESSIONID={jsessionid}'
    }
    
    data = {
        'id': 'get_holidays',
        'method': 'getHolidays',
        'params': {},
        'jsonrpc': '2.0'
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

async def get_timetable_rest_class(credentinals, classID, start_date, end_date):
    url = f"{SERVER_URL}/WebUntis/api/rest/view/v1/timetable/entries?start={start_date.isoformat()}&end={end_date.isoformat()}&format=1&resourceType=CLASS&resources={str(classID)}&periodTypes=&timetableType=STANDARD"    
    cookies = {
        'JSESSIONID': credentinals['jsessionid']
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentinals["token"]}',
    }
    
    response = requests.get(url, headers=headers, cookies=cookies)
    #print(response.json())
    return response.json()

async def get_timetable_rest_teacher(credentinals, teacherShort, start_date, end_date):
    # Get all classes
    classes_data = await get_classes(credentinals['jsessionid'])
    timetable = {
        "mo": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "tu": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "we": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "th": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "fr": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        }
    }
    
    # Iterate through each class and search for lessons with the specified teacher
    klasse_id = None
    for klasse in classes_data.get('result', []):
        
        klasse_id = klasse.get('id')
        timetableClass = await get_timetable_rest_class(credentinals, klasse_id, start_date, end_date)
        
        for day in timetableClass.get('days', []):
            for entry in day.get('gridEntries', []):
                if entry.get('position1')[0].get('current'):
                    if entry.get('position1')[0].get('current').get('displayName') == teacherShort:
                        print(f"Found {entry.get('position1')[0].get('current').get('longName')} entry:")
                        
                        startTime = datetime.datetime.fromisoformat(entry.get('duration').get('start')).time()
                        endTime = datetime.datetime.fromisoformat(entry.get('duration').get('end')).time()
                        weekday = datetime.datetime.fromisoformat(day.get('date')).weekday()
                        match weekday:
                            case 0:
                                weekdayStr = "Monday"
                                weekdayStrShort = "mo"
                            case 1:
                                weekdayStr = "Tuesday"
                                weekdayStrShort = "tu"
                            case 2:
                                weekdayStr = "Wednesday"
                                weekdayStrShort = "we"
                            case 3:
                                weekdayStr = "Thursday"
                                weekdayStrShort = "th"
                            case 4:
                                weekdayStr = "Friday"
                                weekdayStrShort = "fr"
                        subjectShort = entry.get('position2')[0].get('current').get('shortName')
                        subjectLong = entry.get('position2')[0].get('current').get('longName')
                        start_lesson, end_lesson = await time_grid_number(startTime, endTime)
                        if entry.get('position3'):
                            room = entry.get('position3')[0].get('current').get('shortName')
                            timetable[weekdayStrShort][start_lesson]["room"] = room
                        ltype = entry.get('type')
                        status = entry.get('status')                            
                        
                        timetable[weekdayStrShort][start_lesson]["teacher"] = teacherShort
                        timetable[weekdayStrShort][start_lesson]["teacherShort"] = teacherShort
                        timetable[weekdayStrShort][start_lesson]["class"] = klasse.get('name')
                        timetable[weekdayStrShort][start_lesson]["subject"] = subjectShort
                        timetable[weekdayStrShort][start_lesson]["subjectLong"] = subjectLong
                        timetable[weekdayStrShort][start_lesson]["type"] = ltype
                        timetable[weekdayStrShort][start_lesson]["status"] = status
                        if status != "REGULAR":
                            statusDetail = entry.get('statusDetail')
                            timetable[weekdayStrShort][start_lesson]["statusDetail"] = statusDetail
                                
                        if start_lesson == end_lesson:
                            lesson_str = f"lesson {start_lesson}"
                        elif end_lesson - start_lesson == 1:
                            lesson_str = f"lessons {start_lesson} and {end_lesson}"
                            timetable[weekdayStrShort][end_lesson]["teacher"] = teacherShort
                            timetable[weekdayStrShort][end_lesson]["teacherShort"] = teacherShort
                            timetable[weekdayStrShort][end_lesson]["class"] = klasse.get('name')
                            timetable[weekdayStrShort][end_lesson]["subject"] = subjectShort
                            timetable[weekdayStrShort][end_lesson]["subjectLong"] = subjectLong
                            timetable[weekdayStrShort][end_lesson]["room"] = room
                        else:
                            lesson_str = f"lessons {start_lesson} to {end_lesson}"
                        
                        print(subjectLong + ' in class ' + klasse.get('name') + ' in ' + lesson_str + ' on ' + weekdayStr)
    return timetable

async def get_timetable_rest_room(credentinals, roomnumber, start_date, end_date):
    # Get all classes
    classes_data = await get_classes(credentinals['jsessionid'])
    timetable = {
        "mo": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "tu": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "we": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "th": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "fr": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        }
    }
    
    # Iterate through each class and search for lessons with the specified teacher
    klasse_id = None
    for klasse in classes_data.get('result', []):
        
        klasse_id = klasse.get('id')
        timetable_data = await get_timetable_rest_class(credentinals, klasse_id, start_date, end_date)
        
        for day in timetable_data.get('days', []):
            for entry in day.get('gridEntries', []):
                if entry.get('position3'):
                    if entry.get('position3')[0].get('current'):
                        if str(entry.get('position3')[0].get('current').get('shortName')) == roomnumber:
                            print(f"Found {str(entry.get('position3')[0].get('current').get('displayName'))} entry:")
                            
                            startTime = datetime.datetime.fromisoformat(entry.get('duration').get('start')).time()
                            endTime = datetime.datetime.fromisoformat(entry.get('duration').get('end')).time()
                            
                            weekday = datetime.datetime.fromisoformat(day.get('date')).weekday()
                            match weekday:
                                case 0:
                                    weekdayStr = "Monday"
                                    weekdayStrShort = "mo"
                                case 1:
                                    weekdayStr = "Tuesday"
                                    weekdayStrShort = "tu"
                                case 2:
                                    weekdayStr = "Wednesday"
                                    weekdayStrShort = "we"
                                case 3:
                                    weekdayStr = "Thursday"
                                    weekdayStrShort = "th"
                                case 4:
                                    weekdayStr = "Friday"
                                    weekdayStrShort = "fr"
                            subjectShort = entry.get('position2')[0].get('current').get('shortName')
                            subjectLong = entry.get('position2')[0].get('current').get('longName')
                            teacherShort = entry.get('position1')[0].get('current').get('shortName')
                            teacherLong = entry.get('position1')[0].get('current').get('longName')
                            start_lesson, end_lesson = await time_grid_number(startTime, endTime)
                            room = entry.get('position3')[0].get('current').get('shortName')
                            ltype = entry.get('type')
                            status = entry.get('status')
                            if status != "REGULAR":
                                statusDetail = entry.get('statusDetail')
                            timetable[weekdayStrShort][start_lesson]["teacher"] = teacherShort
                            timetable[weekdayStrShort][start_lesson]["teacherShort"] = teacherLong
                            timetable[weekdayStrShort][start_lesson]["class"] = klasse.get('name')
                            timetable[weekdayStrShort][start_lesson]["subject"] = subjectShort
                            timetable[weekdayStrShort][start_lesson]["subjectLong"] = subjectLong
                            timetable[weekdayStrShort][start_lesson]["room"] = room
                            if start_lesson == end_lesson:
                                lesson_str = f"lesson {start_lesson}"
                            elif end_lesson - start_lesson == 1:
                                lesson_str = f"lessons {start_lesson} and {end_lesson}"
                                timetable[weekdayStrShort][end_lesson]["teacher"] = teacherShort
                                timetable[weekdayStrShort][end_lesson]["teacherShort"] = teacherLong
                                timetable[weekdayStrShort][end_lesson]["class"] = klasse.get('name')
                                timetable[weekdayStrShort][end_lesson]["subject"] = subjectShort
                                timetable[weekdayStrShort][end_lesson]["subjectLong"] = subjectLong
                                timetable[weekdayStrShort][end_lesson]["room"] = room
                            else:
                                lesson_str = f"lessons {start_lesson} to {end_lesson}"
                            
                            start_lesson, end_lesson = await time_grid_number(startTime, endTime)
                            
                            if start_lesson == end_lesson:
                                lesson_str = f"lesson {start_lesson}"
                            else:
                                lesson_str = f"lessons {start_lesson} to {end_lesson}"
                            
                            print(entry.get('position3')[0].get('current').get('displayName') + ' in class ' + klasse.get('name') + ' in ' + lesson_str + ' on ' + weekdayStr)
                    elif entry.get("position3")[0].get("removed"):
                        print("no active room")
    return timetable

async def parse_timetable_rest(timetableJSON):
    timetable = {
        "mo": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "tu": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "we": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "th": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        },
        "fr": {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
            7: {},
            8: {},
            9: {},
            10: {},
            11: {}
        }
    }
    
    for day in timetableJSON.get('days', []):
        for entry in day.get('gridEntries', []):
            startTime = datetime.datetime.fromisoformat(entry.get('duration').get('start')).time()
            endTime = datetime.datetime.fromisoformat(entry.get('duration').get('end')).time()
            weekday = datetime.datetime.fromisoformat(day.get('date')).weekday()
            match weekday:
                    case 0:
                        weekdayStr = "Monday"
                        weekdayStrShort = "mo"
                    case 1:
                        weekdayStr = "Tuesday"
                        weekdayStrShort = "tu"
                    case 2:
                        weekdayStr = "Wednesday"
                        weekdayStrShort = "we"
                    case 3:
                        weekdayStr = "Thursday"
                        weekdayStrShort = "th"
                    case 4:
                        weekdayStr = "Friday"
                        weekdayStrShort = "fr"
            subjectShort = entry.get('position2')[0].get('current').get('shortName')
            subjectLong = entry.get('position2')[0].get('current').get('longName')
            start_lesson, end_lesson = await time_grid_number(startTime, endTime)
            className = day.get("resource").get("shortName")
            room = entry.get('position3')[0].get('current').get('shortName')
            ltype = entry.get('type')
            status = entry.get('status')
            
            timetable[weekdayStrShort][start_lesson]["class"] = className
            timetable[weekdayStrShort][start_lesson]["subject"] = subjectShort
            timetable[weekdayStrShort][start_lesson]["subjectLong"] = subjectLong
            timetable[weekdayStrShort][start_lesson]["room"] = room
            timetable[weekdayStrShort][start_lesson]["type"] = ltype
            timetable[weekdayStrShort][start_lesson]["status"] = status
            if status != "REGULAR":
                statusDetail = entry.get('statusDetail')
            if entry.get('position1')[0].get('current'):
                
                teacher = entry.get('position1')[0].get('current').get('longName')
                teacherShort = entry.get('position1')[0].get('current').get('shortName')
                timetable[weekdayStrShort][start_lesson]["teacher"] = teacher
                timetable[weekdayStrShort][start_lesson]["teacherShort"] = teacherShort
                if status != "REGULAR":
                    timetable[weekdayStrShort][start_lesson]["statusDetail"] = statusDetail
                
                if start_lesson == end_lesson:
                    lesson_str = f"lesson {start_lesson}"
                else:
                    if end_lesson - start_lesson == 1:
                        lesson_str = f"lessons {start_lesson} and {end_lesson}"
                    else:
                        lesson_str = f"lessons {start_lesson} to {end_lesson}"
                    timetable[weekdayStrShort][end_lesson]["teacher"] = teacherShort
                    timetable[weekdayStrShort][end_lesson]["teacherShort"] = teacherShort
                    timetable[weekdayStrShort][end_lesson]["class"] = className
                    timetable[weekdayStrShort][end_lesson]["subject"] = subjectShort
                    timetable[weekdayStrShort][end_lesson]["room"] = room
            elif entry.get("position1")[0].get("removed"):
                print("placeholder")
                
    return timetable

async def last_update(credentinals):
    url = f"{SERVER_URL}/WebUntis/main.do"
    cookies = {
        'JSESSIONID': credentinals['jsessionid']
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentinals["token"]}',
    }
    
    response = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, 'html.parser')
    last_update_element = soup.find(string=re.compile("Letzte Planaktualisierung aus Untis"))
    last_update_string = re.sub(r'Letzte Planaktualisierung aus Untis: .*, ', '', last_update_element)
    last_update = datetime.datetime.strptime(last_update_string, '%d.%m.%Y %H:%M:%S')
    
    return last_update

async def main():
    try:
        # Generate OTP token
        token = await get_otp_token()
        
        # Get current timestamp in milliseconds
        current_time = int(datetime.datetime.now().timestamp() * 1000)
        
        # Login to WebUntis
        print("Logging in to WebUntis...")
        credentinals = await login(SCHOOL, SERVER_URL, token, USERNAME, current_time)
        jsessionid = credentinals['jsessionid']
        last_update_data = await last_update(credentinals)
        print(f"Login successful. Session ID: {jsessionid}")
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        friday = monday + datetime.timedelta(days=4)
        print(f"Fetching timetable from {monday} to {friday}...")
        timetable_data = await get_timetable_rest_room(credentinals, 'B305', monday, friday)
        #timetable_data = await get_timetable_rest_teacher(credentinals, 'JANM', monday, friday)
        with open('timetable2.json', 'w', encoding='utf-8') as f:
            json.dump(timetable_data, f, ensure_ascii=False, indent=4)
        print("Timetable saved to timetable2.json")
        timetable_data = await get_timetable_rest_class(credentinals, 4434, monday, friday)
        with open('timetable.json', 'w', encoding='utf-8') as f:
            json.dump(timetable_data, f, ensure_ascii=False, indent=4)
        print("Timetable saved to timetable.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())