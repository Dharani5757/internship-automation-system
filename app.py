
import streamlit as st
import sqlite3
import pandas as pd
import os
import re
import smtplib
from email.message import EmailMessage
from datetime import date, time, datetime, timedelta

st.set_page_config(
    page_title="Internship Automation System",
    layout="wide"
)

DB = "interns.db"


def connect():
    return sqlite3.connect(DB)


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS interns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                college TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT '',
                start_date TEXT NOT NULL DEFAULT '',
                github TEXT NOT NULL DEFAULT ''
            )
        """)

        # Add missing columns if an older database exists
        columns = [
            row[1] for row in
            con.execute("PRAGMA table_info(interns)").fetchall()
        ]
        for col in ["department", "start_date", "github"]:
            if col not in columns:
                con.execute(
                    f"ALTER TABLE interns ADD COLUMN {col} TEXT DEFAULT ''"
                )

        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intern_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                explanation TEXT,
                purpose TEXT,
                tools TEXT,
                steps TEXT,
                deliverables TEXT,
                deadline TEXT,
                review_datetime TEXT,
                meet_link TEXT,
                submission_url TEXT DEFAULT '',
                status TEXT DEFAULT 'Assigned',
                feedback TEXT DEFAULT '',
                verified TEXT DEFAULT 'Pending',
                FOREIGN KEY(intern_id) REFERENCES interns(id)
            )
        """)


def send_task_email(to_email, intern_name, title, explanation,
                    purpose, tools, steps, deliverables,
                    deadline, review_datetime, meet_link):
    # Configure these environment variables before sending emails.
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", username or "")

    if not all([host, username, password, sender]):
        return False, "Email settings are not configured."

    msg = EmailMessage()
    msg["Subject"] = f"Internship Task: {title}"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(f"""
Hi {intern_name},

Your new internship task has been assigned.

Task: {title}

Explanation:
{explanation}

Purpose:
{purpose}

Tools:
{tools}

Steps:
{steps}

Expected deliverables:
{deliverables}

Deadline: {deadline}
Review date and time: {review_datetime}
Google Meet link: {meet_link or "Not provided"}

Please submit your work using your GitHub repository link.

Regards,
Internship Team
""")

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return True, "Email sent successfully."
    except Exception as exc:
        return False, f"Email could not be sent: {exc}"


init_db()

st.title("Internship Automation System")
st.caption("Intern management • Task assignment • Reviews • Feedback")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Dashboard",
    "Add Intern",
    "Assign Task",
    "Review & Feedback",
    "Interns & Tasks"
])

with tab1:
    with connect() as con:
        interns = pd.read_sql_query("SELECT * FROM interns", con)
        tasks = pd.read_sql_query("""
            SELECT t.*, i.name AS intern_name, i.email
            FROM tasks t
            JOIN interns i ON t.intern_id = i.id
            ORDER BY t.id DESC
        """, con)

    a, b, c, d = st.columns(4)
    a.metric("Total Interns", len(interns))
    b.metric("Tasks Assigned", len(tasks))
    c.metric(
        "Upcoming Reviews",
        int((tasks["status"] != "Completed").sum())
        if not tasks.empty else 0
    )
    d.metric(
        "Completed Tasks",
        int((tasks["status"] == "Completed").sum())
        if not tasks.empty else 0
    )

    st.subheader("Upcoming Review Schedule")
    if tasks.empty:
        st.info("No tasks yet. Add an intern and assign a task.")
    else:
        schedule = tasks[tasks["status"] != "Completed"].copy()
        if not schedule.empty:
            st.dataframe(
                schedule[[
                    "intern_name", "title", "deadline",
                    "review_datetime", "meet_link", "status"
                ]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("All tasks are marked completed.")

with tab2:
    st.subheader("Register a New Intern")

    with st.form("add_intern_form"):
        name = st.text_input("Intern full name *")
        email = st.text_input("Email address *")
        college = st.text_input("College name *")
        department = st.text_input("Department")
        github = st.text_input("GitHub username or profile URL")
        start_date = st.date_input("Internship start date", value=date.today())

        save_intern = st.form_submit_button("Save Intern")

    if save_intern:
        if not all([name.strip(), email.strip(), college.strip()]):
            st.error("Name, email and college are required.")
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
            st.error("Enter a valid email address.")
        else:
            try:
                with connect() as con:
                    con.execute("""
                        INSERT INTO interns
                        (name, email, college, department, start_date, github)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        name.strip(), email.strip().lower(),
                        college.strip(), department.strip(),
                        str(start_date), github.strip()
                    ))
                st.success("Intern saved successfully!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("This email address already exists.")

with tab3:
    st.subheader("Assign an Internship Task")

    with connect() as con:
        intern_rows = con.execute(
            "SELECT id, name, email FROM interns ORDER BY name"
        ).fetchall()

    if not intern_rows:
        st.warning("First, add an intern in the Add Intern tab.")
    else:
        intern_options = {
            f"{row[1]} — {row[2]}": row[0] for row in intern_rows
        }

        with st.form("assign_task_form"):
            selected_intern = st.selectbox(
                "Select intern", list(intern_options.keys())
            )
            title = st.text_input("Task title *")
            explanation = st.text_area("Task explanation *")
            purpose = st.text_area("Purpose — why this task matters")
            tools = st.text_input("Tools / technologies to use")
            steps = st.text_area("Step-by-step instructions")
            deliverables = st.text_area(
                "Expected deliverables / submission requirements"
            )

            deadline_date = st.date_input(
                "Task deadline date",
                value=date.today() + timedelta(days=7)
            )
            deadline_time = st.time_input(
                "Task deadline time", value=time(17, 0)
            )

            review_date = st.date_input(
                "Review date",
                value=date.today() + timedelta(days=2)
            )
            review_time = st.time_input(
                "Review time", value=time(10, 0)
            )
            meet_link = st.text_input("Google Meet link")

            send_email = st.checkbox(
                "Send task details by email (requires SMTP setup)"
            )
            assign = st.form_submit_button("Assign Task")

        if assign:
            if not title.strip() or not explanation.strip():
                st.error("Task title and explanation are required.")
            else:
                deadline = datetime.combine(
                    deadline_date, deadline_time
                ).strftime("%Y-%m-%d %H:%M")
                review_datetime = datetime.combine(
                    review_date, review_time
                ).strftime("%Y-%m-%d %H:%M")

                if review_datetime < datetime.now().strftime("%Y-%m-%d %H:%M"):
                    st.error("Choose a review date and time in the future.")
                else:
                    intern_id = intern_options[selected_intern]
                    with connect() as con:
                        con.execute("""
                            INSERT INTO tasks (
                                intern_id, title, explanation, purpose,
                                tools, steps, deliverables, deadline,
                                review_datetime, meet_link
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            intern_id, title.strip(), explanation.strip(),
                            purpose, tools, steps, deliverables,
                            deadline, review_datetime, meet_link.strip()
                        ))

                    st.success("Task assigned and schedule saved.")

                    if send_email:
                        intern = next(
                            row for row in intern_rows
                            if row[0] == intern_id
                        )
                        ok, message = send_task_email(
                            intern[2], intern[1], title, explanation,
                            purpose, tools, steps, deliverables,
                            deadline, review_datetime, meet_link
                        )
                        if ok:
                            st.success(message)
                        else:
                            st.warning(message)

                    st.rerun()

with tab4:
    st.subheader("Update Submission, Review and Feedback")

    with connect() as con:
        task_rows = con.execute("""
            SELECT t.id, t.title, i.name, i.email, t.status,
                   t.submission_url, t.verified, t.feedback
            FROM tasks t
            JOIN interns i ON t.intern_id = i.id
            ORDER BY t.id DESC
        """).fetchall()

    if not task_rows:
        st.info("No assigned tasks available to review.")
    else:
        task_options = {
            f"Task #{r[0]} — {r[2]} — {r[1]}": r[0]
            for r in task_rows
        }

        selected_task = st.selectbox(
            "Select task to review", list(task_options.keys())
        )
        task_id = task_options[selected_task]
        current = next(r for r in task_rows if r[0] == task_id)

        with st.form("review_form"):
            submission_url = st.text_input(
                "GitHub submission URL", value=current[5] or ""
            )
            verified = st.selectbox(
                "GitHub submission verification",
                ["Pending", "Verified", "Needs correction"],
                index=(
                    ["Pending", "Verified", "Needs correction"].index(current[6])
                    if current[6] in ["Pending", "Verified", "Needs correction"]
                    else 0
                )
            )
            status = st.selectbox(
                "Task status",
                ["Assigned", "Submitted", "In Review", "Needs Improvement", "Completed"],
                index=(
                    ["Assigned", "Submitted", "In Review", "Needs Improvement", "Completed"].index(current[4])
                    if current[4] in ["Assigned", "Submitted", "In Review", "Needs Improvement", "Completed"]
                    else 0
                )
            )
            feedback = st.text_area(
                "Review feedback and improvement suggestions",
                value=current[7] or ""
            )
            update_review = st.form_submit_button("Save Review")

        if update_review:
            if submission_url.strip() and not re.match(
                r"^https?://", submission_url.strip()
            ):
                st.error("Submission URL must start with http:// or https://")
            else:
                with connect() as con:
                    con.execute("""
                        UPDATE tasks
                        SET submission_url=?, verified=?, status=?, feedback=?
                        WHERE id=?
                    """, (
                        submission_url.strip(), verified,
                        status, feedback.strip(), task_id
                    ))
                st.success("Review and feedback saved.")
                st.rerun()

with tab5:
    st.subheader("Intern Directory")
    with connect() as con:
        intern_data = pd.read_sql_query("""
            SELECT id, name, email, college, department, start_date, github
            FROM interns ORDER BY id DESC
        """, con)

        task_data = pd.read_sql_query("""
            SELECT t.id AS task_id, i.name AS intern, i.email,
                   t.title, t.deadline, t.review_datetime,
                   t.meet_link, t.submission_url, t.verified,
                   t.status, t.feedback
            FROM tasks t
            JOIN interns i ON t.intern_id = i.id
            ORDER BY t.id DESC
        """, con)

    st.write("**Intern details**")
    st.dataframe(intern_data, use_container_width=True, hide_index=True)
    st.write("**Task and review details**")
    st.dataframe(task_data, use_container_width=True, hide_index=True)

    if not task_data.empty:
        st.download_button(
            "Download task report (CSV)",
            data=task_data.to_csv(index=False).encode("utf-8"),
            file_name="internship_task_report.csv",
            mime="text/csv"
        )
