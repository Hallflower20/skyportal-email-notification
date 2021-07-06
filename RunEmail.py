import schedule
import time
import SendEmailNew

schedule.every().day.at("19:00").do(SendEmailNew.send_email)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except:
        time.sleep(360)
        SendEmailNew.send_email