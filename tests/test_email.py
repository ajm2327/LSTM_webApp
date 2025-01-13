import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def test_email_config():
    try:
        #get settings from environment
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        sender_email = os.getenv('ALERT_EMAIL_SENDER')
        password = os.getenv('ALERT_EMAIL_PASSWORD')
        recipient_email = os.getenv('ALERT_EMAIL_RECIPIENT')

        #create test message
        msg = EmailMessage()
        msg.set_content("This is a test email from your LSTM web app")
        msg['Subject'] = 'LSTM Test Email'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        #send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)

        print("Test email sent successfully")

    except Exception as e:
        print(f"Error sending test email: {str(e)}")

if __name__ == "__main__":
    test_email_config()