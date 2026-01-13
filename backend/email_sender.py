import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔴 CONFIGURATION
SENDER_EMAIL = "dhivyatj20@gmail.com"  # Unga Gmail ID
SENDER_PASSWORD = "kqcp zqqx rdck zoam"    # Replace with App Password

def send_credentials_email(to_email, username, password, access_districts, role_category, existing_issues):
    try:
        subject = f"Appointment: {role_category} Officer - Login Details"
        
        # Format existing issues into a text list
        issues_text = ""
        if existing_issues:
            issues_text = "\n\n🚨 **URGENT PENDING ISSUES FOR YOU:**\n"
            for i, issue in enumerate(existing_issues, 1):
                issues_text += f"{i}. {issue['location']['district']} - {issue['feedback']['original_text']} (Priority: {issue['ai']['priority']})\n"
        else:
            issues_text = "\n\n✅ No pending issues for this category currently."

        body = f"""
        Hello,
        
        You have been appointed as the **{role_category} Officer** for the following districts: {', '.join(access_districts)}.
        
        Here are your login details:
        --------------------------------------------------
        🔗 URL: https://c5ddca62de55993d-223-237-187-214.serveousercontent.com
        👤 Username: {username}
        🔑 Password: {password}
        --------------------------------------------------
        {issues_text}
        
        Please login to the dashboard to take action.
        
        Regards,
        Super Admin Team
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        
        return True, "Email sent successfully!"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"