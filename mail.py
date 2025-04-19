import boto3
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_aws_usage():
    ce = boto3.client('ce', region_name='us-east-1')
    end = datetime.datetime.utcnow().date()
    start = end - datetime.timedelta(days=1)

    report = f"📊 AWS Usage Report for {start.isoformat()}\n\n"
    try:
        # Total cost
        daily_response = ce.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        total = daily_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        report += f"📅 {start.isoformat()} - Total: ${float(total):.2f}\n"

        # Service breakdown
        service_response = ce.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        for group in service_response['ResultsByTime'][0]['Groups']:
            service = group['Keys'][0]
            cost = group['Metrics']['UnblendedCost']['Amount']
            report += f"   └ {service}: ${float(cost):.2f}\n"

        report += "\n"
        return report
    except Exception as e:
        return f"❌ Error retrieving usage: {str(e)}\n"

def get_login_activity():
    cloudtrail = boto3.client('cloudtrail', region_name='us-east-1')
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=1)

    report = "🔐 AWS Console Login Activity (Past 24h):\n\n"
    try:
        events = cloudtrail.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'EventName', 'AttributeValue': 'ConsoleLogin'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50
        )

        if not events['Events']:
            report += "No login events found.\n"
        else:
            for event in events['Events']:
                username = event.get("Username", "Unknown")
                time = event["EventTime"].strftime('%Y-%m-%d %H:%M:%S UTC')
                report += f"🕒 {time} - 👤 {username}\n"

        report += "\n"
        return report
    except Exception as e:
        return f"❌ Error retrieving login activity: {str(e)}\n"

def send_email(report):
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    recipient = os.environ.get("REPORT_RECIPIENT")

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg['Subject'] = "🗓️ AWS Daily Report with Login Activity"
    msg.attach(MIMEText(report, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return "✅ Email sent successfully."
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

if __name__ == "__main__":
    usage_report = get_aws_usage()
    login_report = get_login_activity()
    full_report = usage_report + login_report

    print(full_report)
    result = send_email(full_report)
    print(result)
