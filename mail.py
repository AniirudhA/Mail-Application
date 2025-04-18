#Every past day repports Application
# import boto3
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_aws_usage():
    # Query AWS Cost Explorer: ensure that Cost Explorer is enabled in your account
    ce = boto3.client('ce', region_name='us-east-1')
    end = datetime.datetime.now().date()
    start = end - datetime.timedelta(days=7)  # last 7 days usage
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.isoformat(),
                'End': end.isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        # Process the report to generate a string summary
        report = "AWS Usage Report (Last 7 Days):\n"
        for result in response.get("ResultsByTime", []):
            date = result["TimePeriod"]["Start"]
            cost = result["Total"]['UnblendedCost']['Amount']
            report += f"- {date}: ${cost}\n"

            service_response = ce.get_cost_and_usage(
                TimePeriod={'Start': date, 'End': date},
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
        return report
    except Exception as e:
        return f"Error retrieving usage: {str(e)}"

def send_email(report):
    # Simple email example; you could also use AWS SES for production
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "your_email@example.com")
    smtp_pass = os.environ.get("SMTP_PASS", "your_password")
    recipient = os.environ.get("REPORT_RECIPIENT", "recipient@example.com")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg['Subject'] = "AWS Usage Report"
    msg.attach(MIMEText(report, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

if __name__ == "__main__":
    report = get_aws_usage()
    result = send_email(report)
    print(result)