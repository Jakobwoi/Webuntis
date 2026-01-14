## Kommentare:
## # Kommentare des Autors der QR-Login Funktion(https://github.com/python-webuntis/python-webuntis/issues/47)
## ## Meine Kommentare


import asyncio
import datetime
import webuntis
## wird für den "QR-Code" Login benötigt, ich muss darauf zurückgreifen, da wir keine direkten Logindaten für WebUntis haben
import pyotp
from login import _otpLogin
import Python.login_config as login_config

## Die folgenden Daten werden beim Abrufen des QR-Codes für die Utis-Mobil App angezeigt

# Key used to generate the OTP
## wird als Schlüssel angezeigt
key = login_config.KEY

# WebUntis school name
## wird als Schule angezeigt 
school = login_config.SCHOOL

# WebUntis username
## wird als Benutzer angezeigt
user = login_config.USERNAME

# WebUntis server URL
## wird als Url angezeigt muss (kann gleich bleiben)
url = login_config.SERVER_URL

# Create a TOTP instance with a time window of 30 seconds
totp = pyotp.TOTP(key, interval=30)

# Generate the OTP based on the current timestamp
secret = totp.now()

async def main():
    # Call the _otpLogin function and store the result in a variable
    current_time = int(datetime.datetime.now().timestamp() * 1000)

    s = await _otpLogin(scname=school, server=url, token=secret, username=user, time=current_time)
    ## Tag für den Stundenplan ausgegeben werden soll: -1 = Gestern, 0 = Heute, 1 = Morgen
    days = 7
    today = datetime.date.today()
    monday = today + datetime.timedelta(days=days)
    friday = today + datetime.timedelta(days=days)
    ## sucht meine ID und lädt meinen Stundenplan da ich die Funktion Session.smy_timetable() nicht verwenden kann, weil ich die Session.login() Funktion nicht verwende
    student_id = s.get_student(surname='Woittennek', fore_name='Jakob').id
    class_id = s.get_class()
    table = s.timetable_extended(student=student_id, start=monday, end=friday).to_table()

    ## gibt (mit meinen Berechtigungen/Login-Daten) ein leeres Objekt zurück
    #print(s.teachers()) 

    ## zeigt das Lehrer tatsächlich über die API abgerufen werden können und existieren
    #print(s.get_teacher(surname='SCHARINGER', fore_name='Stephan')._data)
    ## geht die Stunden durch und gibt sie aus
    for lesson in table:

        tabelelemet = next(iter(lesson[1][0][1]))
        ## Gibt die Stunden im Format "HH:MM - HH:MM Fach Lehrer Raum" aus, da Lehrer nie und Räume nur manchmal vorhanden sind wird hier nicht auf ein Element aus der Liste zugegriffen
        print(tabelelemet.start.strftime('%H:%M') + " - " + tabelelemet.end.strftime('%H:%M') + " " + tabelelemet.subjects[0].name + " " + str(tabelelemet.teachers) + " " + str(tabelelemet.rooms))

# Start the asynchronous task
asyncio.run(main())