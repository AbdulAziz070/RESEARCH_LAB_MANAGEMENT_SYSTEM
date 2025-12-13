from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

# ------------------ DB CONFIG ------------------
db_config = {
    "host": "localhost",
    "database": "research_lab",
    "user": "root",
    "password": "password123"
}

def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"DB ERROR: {e}")
    return None

# ------------------ FLASK APP ------------------
app = Flask(__name__)
app.secret_key = "some-secret-key-change-this"

# ------------------ HOME ------------------
@app.route("/")
def index():
    return render_template("index.html")

# ==============================
#   PROJECT & MEMBER MANAGEMENT
# ==============================

# --- list members ---
@app.route("/members")
def members():
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))

    cur = conn.cursor()
    cur.execute("""
        SELECT L.MID, L.Name, L.JoinDate, L.MType, L.Mentor, S.Major
        FROM LAB_MEMBER L
        LEFT JOIN STUDENT S ON L.MID = S.MID
        ORDER BY L.MID
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("members.html", members=rows)

# --- add member ---
@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        mid = request.form.get("mid")
        name = request.form.get("name")
        joindate = request.form.get("joindate")
        mtype = request.form.get("mtype")
        mentor = request.form.get("mentor") or None
        major = request.form.get("major") or None

        conn = get_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("members"))

        cur = conn.cursor()
        try:
            if mid and mid.strip() != "":
                cur.execute(
                    "INSERT INTO LAB_MEMBER (MID, Name, JoinDate, MType, Mentor) VALUES (%s, %s, %s, %s, %s)",
                    (mid, name, joindate, mtype, mentor),
                )
                created_id = mid
            else:
                cur.execute(
                    "INSERT INTO LAB_MEMBER (Name, JoinDate, MType, Mentor) VALUES (%s, %s, %s, %s)",
                    (name, joindate, mtype, mentor),
                )
                created_id = cur.lastrowid

            if mtype and mtype.lower() == "student" and major:
                cur.execute(
                    "INSERT INTO STUDENT (MID, Major) VALUES (%s, %s)",
                    (created_id, major),
                )

            conn.commit()
            flash(f"Member added successfully ✅ (MID: {created_id})", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error adding member: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("members"))

    return render_template("member_form.html", mode="add")

# --- edit member (GET/POST) ---
@app.route("/members/edit/<int:mid>", methods=["GET", "POST"])
def edit_member(mid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("members"))

    cur = conn.cursor()
    if request.method == "POST":
        name = request.form.get("name")
        joindate = request.form.get("joindate")
        mtype = request.form.get("mtype")
        mentor = request.form.get("mentor") or None
        major = request.form.get("major") or None
        try:
            cur.execute("UPDATE LAB_MEMBER SET Name=%s, JoinDate=%s, MType=%s, Mentor=%s WHERE MID=%s",
                        (name, joindate, mtype, mentor, mid))
            if mtype and mtype.lower() == "student":
                cur.execute("SELECT MID FROM STUDENT WHERE MID=%s", (mid,))
                if cur.fetchone():
                    cur.execute("UPDATE STUDENT SET Major=%s WHERE MID=%s", (major, mid))
                else:
                    if major:
                        cur.execute("INSERT INTO STUDENT (MID, Major) VALUES (%s, %s)", (mid, major))
            else:
                cur.execute("DELETE FROM STUDENT WHERE MID=%s", (mid,))
            conn.commit()
            flash("Member updated ✅", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error updating member: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("members"))

    cur.execute("SELECT L.MID, L.Name, L.JoinDate, L.MType, L.Mentor, S.Major FROM LAB_MEMBER L LEFT JOIN STUDENT S ON L.MID=S.MID WHERE L.MID=%s", (mid,))
    member = cur.fetchone()
    cur.close()
    conn.close()
    if not member:
        flash("Member not found", "warning")
        return redirect(url_for("members"))
    return render_template("member_form.html", mode="edit", member=member)

# --- remove member ---
@app.route("/members/delete/<int:mid>", methods=["POST", "GET"])
def delete_member(mid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("members"))

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM STUDENT WHERE MID = %s", (mid,))
        cur.execute("DELETE FROM WORKS WHERE MID = %s", (mid,))
        cur.execute("DELETE FROM USES WHERE MID = %s", (mid,))
        cur.execute("DELETE FROM PUBLISHES WHERE MID = %s", (mid,))
        cur.execute("DELETE FROM LAB_MEMBER WHERE MID = %s", (mid,))
        conn.commit()
        flash("Member deleted ✅", "success")
    except Error as e:
        conn.rollback()
        flash(f"Error deleting member: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("members"))

# ==============================
#        PROJECT ROUTES
# ==============================

import logging
# optional: configure logging to stdout (helps in Windows console)
logging.basicConfig(level=logging.INFO)

# --- list projects + status ---
@app.route("/projects")
def projects():
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))

    cur = conn.cursor()
    cur.execute("""
        SELECT P.PID, P.Title, P.SDate, P.EDate,
               L.Name AS LeaderName
        FROM PROJECT P
        LEFT JOIN LAB_MEMBER L ON P.Leader = L.MID
        ORDER BY P.PID
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("projects.html", projects=rows)


# --- add project (GET + POST) ---
@app.route("/projects/add", methods=["GET", "POST"])
def add_project():
    if request.method == "POST":
        pid = request.form.get("pid")
        title = request.form.get("title")
        sdate = request.form.get("sdate")
        edate = request.form.get("edate") or None
        leader = request.form.get("leader") or None

        conn = get_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("projects"))

        cur = conn.cursor()
        try:
            if pid and pid.strip() != "":
                cur.execute(
                    "INSERT INTO PROJECT (PID, Title, SDate, EDate, Leader) VALUES (%s, %s, %s, %s, %s)",
                    (pid, title, sdate, edate, leader),
                )
                created_pid = pid
            else:
                cur.execute(
                    "INSERT INTO PROJECT (Title, SDate, EDate, Leader) VALUES (%s, %s, %s, %s)",
                    (title, sdate, edate, leader),
                )
                created_pid = cur.lastrowid

            conn.commit()
            flash(f"Project created ✅ (PID: {created_pid})", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error creating project: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("projects"))

    return render_template("project_form.html", project=None)


# --- edit project (GET/POST) ---
@app.route("/projects/edit/<int:pid>", methods=["GET", "POST"])
def edit_project(pid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("projects"))

    cur = conn.cursor()
    if request.method == "POST":
        title = request.form.get("title")
        sdate = request.form.get("sdate")
        edate = request.form.get("edate") or None
        leader = request.form.get("leader") or None
        try:
            cur.execute("UPDATE PROJECT SET Title=%s, SDate=%s, EDate=%s, Leader=%s WHERE PID=%s",
                        (title, sdate, edate, leader, pid))
            conn.commit()
            flash("Project updated ✅", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error updating project: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("projects"))

    cur.execute("SELECT PID, Title, SDate, EDate, Leader FROM PROJECT WHERE PID=%s", (pid,))
    project = cur.fetchone()
    cur.close()
    conn.close()
    if not project:
        flash("Project not found", "warning")
        return redirect(url_for("projects"))
    return render_template("project_form.html", project=project)


# --- delete project (safe delete) ---
@app.route("/projects/delete/<int:pid>", methods=["POST"])
def delete_project(pid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("projects"))

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM PROJECT WHERE PID = %s", (pid,))
        conn.commit()

        if cur.rowcount == 0:
            flash("Project not found.", "warning")
        else:
            flash("Project deleted ✅", "success")

    except Error as e:
        conn.rollback()
        flash(f"Error deleting project: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("projects"))


# --- project status (via PID search) ---
@app.route("/projects/status", methods=["POST"])
def project_status():
    pid = request.form.get("pid")
    if not pid:
        flash("Please provide a project ID", "warning")
        return redirect(url_for("projects"))

    # convert to int safely
    try:
        pid_int = int(pid)
    except (ValueError, TypeError):
        flash("Invalid project ID", "danger")
        return redirect(url_for("projects"))

    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("projects"))

    cur = conn.cursor()
    try:
        cur.execute("SELECT Title, SDate, EDate FROM PROJECT WHERE PID = %s", (pid_int,))
        row = cur.fetchone()
    except Error as e:
        row = None
        flash(f"Error fetching project status: {e}", "warning")
    finally:
        cur.close()
        conn.close()

    if not row:
        flash("Project not found", "warning")
    else:
        title, sdate, edate = row
        status = "Active" if edate is None else f"Ended on {edate}"
        flash(f"{title} | Started {sdate} | Status: {status}", "info")
    return redirect(url_for("projects"))



# ====================
#   EQUIPMENT MODULE
# ====================

@app.route("/equipment")
def equipment():
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))

    cur = conn.cursor()
    # include Purpose and PDate so edit form can prefill them
    cur.execute("SELECT EID, EName, EType, Status, PDate FROM EQUIPMENT ORDER BY EID")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("equipment.html", equipment=rows)

@app.route("/equipment/add", methods=["GET", "POST"])
def add_equipment():
    if request.method == "POST":
        eid = request.form.get("eid")
        name = request.form.get("name")
        etype = request.form.get("etype")
        status = (request.form.get("status") or "Active").strip()
        purpose = request.form.get("purpose")
        

        # canonicalize status
        if status.lower() in {"maintenance", "under maintenance", "maint"}:
            status = "Maintenance"
        ALLOWED = {"Active", "Maintenance", "Retired"}
        if status not in ALLOWED:
            flash(f"Invalid status value: {status}. Allowed: {', '.join(ALLOWED)}", "danger")
            return redirect(url_for("add_equipment"))

        conn = get_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("equipment"))

        cur = conn.cursor()
        try:
            if eid and eid.strip() != "":
                cur.execute(
                    "INSERT INTO EQUIPMENT (EID, EName, EType, Status, Purpose, PDate) VALUES (%s, %s, %s, %s, %s, CURDATE())",
                    (eid, name, etype, status, purpose),
                )
                created_eid = eid
            else:
                cur.execute(
                    "INSERT INTO EQUIPMENT (EName, EType, Status, Purpose, PDate) VALUES (%s, %s, %s, %s, CURDATE())",
                    (name, etype, status, purpose),
                )
                created_eid = cur.lastrowid

            conn.commit()
            flash(f"Equipment added ✅ (EID: {created_eid}, Status: {status})", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error adding equipment: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("equipment"))

    return render_template("equipment_form.html", mode="add")

@app.route("/equipment/status/<int:eid>", methods=["POST"])
def update_equipment_status(eid):
    status = (request.form.get("status") or "Active").strip()
    if status.lower() in {"maintenance", "under maintenance", "maint"}:
        status = "Maintenance"
    ALLOWED = {"Active", "Maintenance", "Retired"}
    if status not in ALLOWED:
        flash(f"Invalid status value: {status}", "danger")
        return redirect(url_for("equipment"))

    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("equipment"))

    cur = conn.cursor()
    try:
        cur.execute("UPDATE EQUIPMENT SET Status = %s WHERE EID = %s", (status, eid))
        conn.commit()
        flash(f"Status updated to {status} ✅", "success")
    except Error as e:
        conn.rollback()
        flash(f"Error updating equipment: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("equipment"))

@app.route("/equipment/delete/<int:eid>", methods=["POST"])
def delete_equipment(eid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("equipment"))

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM USES WHERE EID = %s", (eid,))
        cur.execute("DELETE FROM EQUIPMENT WHERE EID = %s", (eid,))
        conn.commit()
        flash("Equipment deleted ✅", "success")
    except Error as e:
        conn.rollback()
        flash(f"Error deleting equipment: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("equipment"))

@app.route("/equipment/active_users", methods=["POST"])
def equipment_active_users():
    eid = request.form.get("eid")
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("equipment"))

    cur = conn.cursor()
    cur.execute("""
        SELECT M.Name, P.Title
        FROM USES U
        JOIN LAB_MEMBER M ON U.MID = M.MID
        LEFT JOIN WORKS W ON M.MID = W.MID
        LEFT JOIN PROJECT P ON W.PID = P.PID
        WHERE U.EID = %s AND CURDATE() BETWEEN U.SDate AND U.EDate
    """, (eid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        flash("No active users right now for that equipment.", "info")
    else:
        for name, title in rows:
            flash(f"{name} (Project: {title})", "info")
    return redirect(url_for("equipment"))

# ==========================
#   USES (Equipment Usage) CRUD
# ==========================

@app.route("/uses")
def uses_list():
    eid_filter = request.args.get("eid")
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))
    cur = conn.cursor()
    if eid_filter:
        cur.execute("""SELECT U.MID, L.Name, U.EID, E.EName, U.SDate, U.EDate, U.Purpose
                       FROM USES U
                       JOIN LAB_MEMBER L ON U.MID=L.MID
                       JOIN EQUIPMENT E ON U.EID=E.EID
                       WHERE U.EID=%s
                       ORDER BY U.SDate DESC""", (eid_filter,))
    else:
        cur.execute("""SELECT U.MID, L.Name, U.EID, E.EName, U.SDate, U.EDate, U.Purpose
                       FROM USES U
                       JOIN LAB_MEMBER L ON U.MID=L.MID
                       JOIN EQUIPMENT E ON U.EID=E.EID
                       ORDER BY U.SDate DESC""")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("uses_list.html", uses=rows)

@app.route("/uses/add", methods=["GET", "POST"])
def add_uses():
    if request.method == "POST":
        mid = request.form.get("mid")
        eid = request.form.get("eid")
        sdate = request.form.get("sdate")
        edate = request.form.get("edate") or None
        purpose = (request.form.get("purpose") or None)

        conn = get_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("uses_list"))
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO USES (MID, EID, SDate, EDate, Purpose) VALUES (%s,%s,%s,%s,%s)", (mid, eid, sdate, edate, purpose))
            conn.commit()
            flash("Usage added ✅", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error adding usage: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("uses_list"))
    eid_prefill = request.args.get("eid")
    return render_template("uses_form.html", mode="add", record=None, eid_prefill=eid_prefill)

@app.route("/uses/edit", methods=["GET", "POST"])
def edit_uses():
    mid = request.args.get("mid")
    eid = request.args.get("eid")
    sdate = request.args.get("sdate")
    purpose = (request.args.get("purpose") or None)
    if not (mid and eid and sdate):
        flash("Missing parameters to edit usage.", "warning")
        return redirect(url_for("uses_list"))

    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("uses_list"))

    cur = conn.cursor()
    if request.method == "POST":
        new_sdate = request.form.get("sdate")
        new_edate = request.form.get("edate") or None
        purpose = (request.form.get("purpose") or None)
        try:
            if new_sdate != sdate:
                cur.execute("DELETE FROM USES WHERE MID=%s AND EID=%s AND SDate=%s", (mid, eid, sdate))
                cur.execute("INSERT INTO USES (MID, EID, SDate, EDate, Purpose) VALUES (%s,%s,%s,%s,%s)",
                            (mid, eid, new_sdate, new_edate, purpose))
            else:
                cur.execute("UPDATE USES SET EDate=%s, Purpose=%s WHERE MID=%s AND EID=%s AND SDate=%s",
                            (new_edate, purpose, mid, eid, sdate))
            conn.commit()
            flash("Usage updated ✅", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error updating usage: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("uses_list"))

    cur.execute("SELECT MID, EID, SDate, EDate, Purpose FROM USES WHERE MID=%s AND EID=%s AND SDate=%s", (mid, eid, sdate))
    record = cur.fetchone()
    cur.close()
    conn.close()
    if not record:
        flash("Usage record not found.", "warning")
        return redirect(url_for("uses_list"))
    return render_template("uses_form.html", mode="edit", record=record)

@app.route("/uses/delete", methods=["POST"])
def delete_uses():
    mid = request.form.get("mid")
    eid = request.form.get("eid")
    sdate = request.form.get("sdate")
    if not (mid and eid and sdate):
        flash("Missing parameters for delete.", "warning")
        return redirect(url_for("uses_list"))

    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("uses_list"))
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM USES WHERE MID=%s AND EID=%s AND SDate=%s", (mid, eid, sdate))
        conn.commit()
        flash("Usage deleted ✅", "success")
    except Error as e:
        conn.rollback()
        flash(f"Error deleting usage: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("uses_list"))

# ==========================
#   REPORTS & ANALYTICS
# ==========================

@app.route("/reports", methods=["GET", "POST"])
def reports():
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))

    ctx = {
        "top_publisher": None,
        "avg_per_major": [],
        "top_for_grant": [],
        "active_projects": []
    }

    cur = conn.cursor()

    # 1. Member with highest publications
    try:
        cur.execute("""
            SELECT M.Name, COUNT(PB.PubID) as C
            FROM LAB_MEMBER M
            JOIN PUBLISHES PB ON M.MID = PB.MID
            GROUP BY M.MID
            ORDER BY C DESC
            LIMIT 1
        """)
        ctx["top_publisher"] = cur.fetchone()
    except Error:
        try:
            cur.execute("""
                SELECT M.Name, COUNT(*) as C
                FROM LAB_MEMBER M
                JOIN PUBLISHES PB ON M.MID = PB.MID
                GROUP BY M.MID
                ORDER BY C DESC
                LIMIT 1
            """)
            ctx["top_publisher"] = cur.fetchone()
        except Error as e:
            ctx["top_publisher"] = None
            flash(f"Report query error (top publisher): {e}", "warning")

    # 2. Average student publications per major
    try:
        cur.execute("""
            SELECT S.Major, COUNT(Pub.PubID) / COUNT(DISTINCT S.MID) as avg_pub
            FROM STUDENT S
            JOIN PUBLISHES Pub ON S.MID = Pub.MID
            JOIN PUBLICATION PubInfo ON Pub.PubID = PubInfo.PubID
            GROUP BY S.Major
        """)
        ctx["avg_per_major"] = cur.fetchall()
    except Error:
        try:
            cur.execute("""
                SELECT S.Major, COUNT(Pub.MID) / COUNT(DISTINCT S.MID) as avg_pub
                FROM STUDENT S
                JOIN PUBLISHES Pub ON S.MID = Pub.MID
                GROUP BY S.Major
            """)
            ctx["avg_per_major"] = cur.fetchall()
        except Error as e:
            ctx["avg_per_major"] = []
            flash(f"Report query error (avg per major): {e}", "warning")

    gid = None
    start = None
    end = None
    if request.method == "POST":
        gid = request.form.get("gid_for_top")
        gid_range = request.form.get("gid_for_range")
        start = request.form.get("start")
        end = request.form.get("end")

        if gid:
            try:
                cur.execute("""
                    SELECT M.Name, COUNT(Pub.PubID) as Pubs
                    FROM FUNDS F
                    JOIN PROJECT P ON F.PID = P.PID
                    JOIN WORKS W ON P.PID = W.PID
                    JOIN LAB_MEMBER M ON W.MID = M.MID
                    JOIN PUBLISHES Pub ON M.MID = Pub.MID
                    WHERE F.GID = %s
                    GROUP BY M.MID
                    ORDER BY Pubs DESC
                    LIMIT 3
                """, (gid,))
                ctx["top_for_grant"] = cur.fetchall()
                ctx["gid_for_top"] = gid
            except Error as e:
                ctx["top_for_grant"] = []
                flash(f"Report query error (top for grant): {e}", "warning")

        if gid_range and start and end:
            try:
                cur.execute("""
                    SELECT P.Title
                    FROM FUNDS F
                    JOIN PROJECT P ON F.PID = P.PID
                    WHERE F.GID = %s AND (P.SDate <= %s AND (P.EDate IS NULL OR P.EDate >= %s))
                """, (gid_range, end, start))
                ctx["active_projects"] = [r[0] for r in cur.fetchall()]
                ctx["gid_for_range"] = gid_range
                ctx["start"] = start
                ctx["end"] = end
            except Error as e:
                ctx["active_projects"] = []
                flash(f"Report query error (active projects): {e}", "warning")

    cur.close()
    conn.close()
    return render_template("reports.html", **ctx)


# ==============================
#      PUBLICATIONS MODULE
# ==============================

@app.route("/publications")
def publications():
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("index"))

    cur = conn.cursor()
    # Fetch publications. 
    # Optional: You could JOIN with PUBLISHES to show author names, 
    # but keeping it simple for the 'quick' fix.
    cur.execute("SELECT PubID, Title, Venue, Date, DOI FROM PUBLICATION ORDER BY Date DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("publications.html", publications=rows)

@app.route("/publications/add", methods=["GET", "POST"])
def add_publication():
    if request.method == "POST":
        title = request.form.get("title")
        venue = request.form.get("venue")
        pdate = request.form.get("date")
        doi = request.form.get("doi") or None
        # We capture one author to satisfy the constraint that every pub has an author
        primary_mid = request.form.get("mid") 

        conn = get_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("publications"))

        cur = conn.cursor()
        try:
            # 1. Insert Publication
            cur.execute(
                "INSERT INTO PUBLICATION (Title, Venue, Date, DOI) VALUES (%s, %s, %s, %s)",
                (title, venue, pdate, doi)
            )
            new_pubid = cur.lastrowid

            # 2. Link to Primary Author (Required by your Schema logic)
            if primary_mid and primary_mid.strip():
                cur.execute(
                    "INSERT INTO PUBLISHES (MID, PubID, SDate, Purpose) VALUES (%s, %s, %s, 'Primary Author')",
                    (primary_mid, new_pubid, pdate)
                )

            conn.commit()
            flash(f"Publication added ✅ (PubID: {new_pubid})", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error adding publication: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("publications"))

    return render_template("publication_form.html", mode="add")

@app.route("/publications/edit/<int:pubid>", methods=["GET", "POST"])
def edit_publication(pubid):
    conn = get_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("publications"))

    cur = conn.cursor()
    if request.method == "POST":
        title = request.form.get("title")
        venue = request.form.get("venue")
        pdate = request.form.get("date")
        doi = request.form.get("doi") or None
        try:
            cur.execute(
                "UPDATE PUBLICATION SET Title=%s, Venue=%s, Date=%s, DOI=%s WHERE PubID=%s",
                (title, venue, pdate, doi, pubid)
            )
            conn.commit()
            flash("Publication updated ✅", "success")
        except Error as e:
            conn.rollback()
            flash(f"Error updating publication: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("publications"))

    # GET
    cur.execute("SELECT PubID, Title, Venue, Date, DOI FROM PUBLICATION WHERE PubID=%s", (pubid,))
    pub = cur.fetchone()
    cur.close()
    conn.close()
    
    if not pub:
        flash("Publication not found", "warning")
        return redirect(url_for("publications"))
        
    return render_template("publication_form.html", mode="edit", pub=pub)

@app.route("/publications/delete/<int:pubid>", methods=["POST"])
def delete_publication(pubid):
    conn = get_connection()
    if not conn:
        return redirect(url_for("publications"))

    cur = conn.cursor()
    try:
        # ON DELETE CASCADE in your schema handles the PUBLISHES links automatically
        cur.execute("DELETE FROM PUBLICATION WHERE PubID = %s", (pubid,))
        conn.commit()
        flash("Publication deleted ✅", "success")
    except Error as e:
        conn.rollback()
        flash(f"Error deleting publication: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("publications"))

if __name__ == "__main__":
    app.run(debug=True)