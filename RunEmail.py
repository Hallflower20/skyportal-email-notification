import schedule
import time
import SendEmailNew
import adjustPriority

schedule.every().day.at("19:00").do(SendEmailNew.send_email)
schedule.every().day.at("19:00").do(adjstPriority.adjust_priority)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except:
        time.sleep(360)
        SendEmailNew.send_email
        adjstPriority.adjust_priority
