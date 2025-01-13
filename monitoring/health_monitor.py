import requests
import time
import smtplib
from email.message import EmailMessage
import logging
import os
from datetime import datetime, timezone
import signal
import sys

class HealthMonitor:
    def __init__(self, base_url, check_interval=300): #5 minutes
        self.base_url = base_url
        self.check_interval = check_interval
        self.running = True
        self.setup_logging()

        # set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def setup_logging(self):
        #create logs directory
        os.makedurs('logs', exist_ok = True)

        #setup file logging
        logging.basicConfig(
            filename = 'logs/monitoring.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        #console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

    def shutdown(self, signum, frame):
        print("\nShutting down monitor...")
        self.running = False

    def send_alert(self, subject, body):
        #configure email settings
        try:
            #Get email settings from enviroment variables
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('ALERT_EMAIL_SENDER')
            sender_password = os.getenv('ALERT_EMAIL_PASSWORD')
            recipient_email = os.getenv('ALERT_EMAIL_RECIPIENT')

            if not all([sender_email, sender_password, recipient_email]):
                logging.warning("Email alert settings not configured")
                return
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = f"LSTM Tool Alert: {subject}"
            msg['From'] = sender_email
            msg['To'] = recipient_email

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                logging.info(f"Alert email sent: {subject}")
        except Exception as e:
            logging.error(f"Failed to send alert email: {str(e)}")

    def check_health(self):
        try:
            print(f"\nPerforming health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            response = requests.get(f"{self.base_url}/health/check")
            health_data = response.json()

            #print overall status
            print(f"Overall status: {health_data['status']}")

            #log component statuses
            for component, data in health_data['components'].items():
                status = data.get('status')
                message = data.get('message', '')

                #print component status with color
                status_color = '\033[92m' if status == 'healthy' else '\033[91m'
                print(f"{component}: {status_color}{status}\033[0m")

                if status != 'healthy':
                    alert_msg = f"Component {component} is {status}: {message}"
                    logging.warning(alert_msg)
                    self.send_alert(
                        f"{component} Health Alert",
                        f"Component: {component}\nStatus: {status}\nMessage: {message}\nTimestamp: {datetime.now(timezone.utc)}"
                    )
                    logging.warning(f"Component {component} status: {status} - {message}")
            
            if health_data['status'] != 'healthy':
                self.send_alert(
                    "System Health Alert",
                    f"Overall system health is {health_data['status']}\nDetails: {health_data}"
                )

            print("-" * 50)
            return health_data
        except Exception as e:
            error_msg = f"Health check error: {str(e)}"
            logging.error(error_msg)
            print(f"\033[91mError: {error_msg}\033[0m")
            self.send_alert("Health Check Error", error_msg)
            return None
        
    def run(self):
        while True:
            self.check_health()
            time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = HealthMonitor("http://localhost:5000")
    monitor.run()