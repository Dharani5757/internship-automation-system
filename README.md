# Internship Task Assignment & Review System

A beginner-friendly local web app to manage interns, assign tasks, send task/feedback emails, track GitHub submission URLs, and manage review schedules without Google Calendar.

## Features
- Add interns individually or bulk-import a CSV.
- Assign a task with objective, tools, steps, deliverables, deadline, review date/time, and optional meeting link.
- Send task emails through Gmail SMTP after configuring credentials.
- Record GitHub repository URLs and check their URL format.
- Track review status and mentor feedback; optionally email feedback.
- View upcoming/overdue reviews and manually send reminders.
- Export intern, task, and email-log data to CSV.
- Uses a local SQLite database.

## Run on Windows 11
1. Install Python 3.10+ from https://www.python.org/downloads/ (enable "Add Python to PATH").
2. Extract the ZIP file.
3. Open Command Prompt in this folder.
4. Run:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   streamlit run app.py
   ```
5. Your browser should open the app. If not, visit the local address printed in the terminal.

## Enable email
1. Open `.env` in Notepad.
2. Set `SMTP_USER` to the Gmail account that will send messages.
3. Set `SMTP_APP_PASSWORD` to a Google App Password if available for the account.
4. Set `EMAIL_FROM` to the sender email.
5. Save and restart the app.
6. First test sending to your own email. Never put your normal Gmail password here.

## Importing 100 interns
Prepare a CSV with these required columns:
- `intern_id`
- `name`
- `email`

Optional columns:
- `skills`
- `start_date`
- `end_date`

Use the **Manage Interns** page to upload the CSV. Test with fake/sample records first.

## Important limitations
- This is a local prototype, not yet a production deployment.
- Review reminders are listed in the app and can be sent manually. Automatic reminders require a persistent scheduler or an automation platform that runs even when your computer is off.
- The app does not create Google Meet links; paste a meeting link into the task.
- GitHub checking validates URL structure only; it does not execute code or confirm project quality.
- Before using real intern data, add authentication, access controls, secure hosting, backups, and a privacy policy.
- Test email sending with your own account before sending bulk emails.

## Suggested next upgrades
- Automated scheduled reminder service.
- GitHub API checks for README, files, commits, and configured tests.
- Mentor login and role-based permissions.
- Task library and skill-based task allocation.
- Internship completion report.
