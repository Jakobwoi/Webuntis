from login import _otpLogin
import datetime
import logging
import pyotp
import asyncio
import Python.login_config as login_config

# ***DO NOT USE THIS EXAMPLE AS-IS***
# Properties that are printed here may contain arbitrary
# *unescaped* HTML. That is not expected, but you should not trust
# input from remote sources in general.

# Key used to generate the OTP
key = login_config.KEY

# WebUntis school name
school = login_config.SCHOOL

# WebUntis username
user = login_config.USERNAME

# WebUntis server URL
url = login_config.SERVER_URL

# Create a TOTP instance with a time window of 30 seconds
totp = pyotp.TOTP(key, interval=30)

# Generate the OTP based on the current timestamp
secret = totp.now()

logging.basicConfig(level=logging.CRITICAL)
async def main():

  current_time = int(datetime.datetime.now().timestamp() * 1000)
  response = await _otpLogin(scname=school, server=url, token=secret, username=user, time=current_time)
  s = response

  today = datetime.date.today()

  monday = today - datetime.timedelta(days=today.weekday())
  friday = monday + datetime.timedelta(days=4)

  klasse = s.klassen().filter(name='6d')[0]
  table = s.timetable(klasse=klasse, start=monday, end=friday).to_table()


  print('<table border="1"><thead><th>Time</th>')
  for weekday in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
      print('<th>' + str(weekday) + '</th>')

  print('</thead><tbody>')
  for time, row in table:
      print('<tr>')
      print('<td>{}</td>'.format(time.strftime('%H:%M')))
      for date, cell in row:
          print('<td>')
          for period in cell:
              print(', '.join(su.name for su in period.subjects))
          print('</td>')

      print('</tr>')

  print('</tbody></table>')
# Start the asynchronous task
asyncio.run(main())
