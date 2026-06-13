import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

def send_daily_nudge(rows, recipient_email, sender_email=None, app_password=None):
    from dotenv import load_dotenv
    import os
    load_dotenv()
    sender_email = sender_email or os.getenv("GMAIL_ID")
    app_password = app_password or os.getenv("GMAIL_PASSWORD")
    today = date.today().isoformat()
    today_tasks = [r for r in rows if r['date'] == today]
    table_rows = "".join(
        f"<tr>"
        f"<td>{r['subject']}</td>"
        f"<td>{r['topic']}</td>"
        f"<td>{r['minutes']} min</td>"
        f"<td><i>{r['notes']}</i></td>"
        f"</tr>"
        for r in today_tasks
    )
    
    total_mins = sum(r['minutes'] for r in today_tasks)
    html = f"""
    <h2>StudyPilot - {today}</h2>
    <table border='1' cellpadding='6'>
    <tr><th>Subject</th><th>Topics</th><th>Time</th><th>Notes</th></tr>
    {table_rows}
    </table>
    <p><strong>Total today: {total_mins} minutes</strong></p>
    <p>Stay consistent. See you tomorrow.</p>
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'studyPilot - Your plan for {today}'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f'Nudge sent to {recipient_email}')