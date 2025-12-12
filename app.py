import mysql.connector
from mysql.connector import Error
import sys
import os
from colorama import init, Fore, Style

init(autoreset=True)

def clear_screen():
    os.system("cls")  # 'clear' if you ever run on Linux

# DATABASE CONFIGURATION
# ⚠️Password must match what you set in Phase 1 / Create_queries.sql
db_config = {
    'host': 'localhost',
    'database': 'research_lab',
    'user': 'root',
    'password': 'password123'
}

def create_connection():
    """ Connect to MySQL Database """
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Connection Failed: {e}")
        return None

def execute_query(conn, query, params=None, is_select=False, return_lastrow=False):
    """
    Helper to run SQL queries.
    - is_select=True -> returns fetched rows (or [] on none)
    - return_lastrow=True -> for INSERTs return cursor.lastrowid (int) after commit
    - otherwise returns True on success, None on exception
    """
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if is_select:
            rows = cursor.fetchall()
            return rows
        else:
            conn.commit()
            if return_lastrow:
                return cursor.lastrowid
            return True
    except Error as e:
        # improved debug message
        print(Fore.RED + "❌ SQL Error:")
        print("    Query: ", query)
        print("    Params:", params)
        print("    Error: ", e)
        return None

# ----------------------------
# CLI: Update Member / Update Project helpers
# ----------------------------
def update_member(conn):
    mid = input("Enter Member ID to update: ")
    res = execute_query(conn, "SELECT MID, Name, JoinDate, MType, Mentor FROM LAB_MEMBER WHERE MID=%s", (mid,), is_select=True)
    if not res:
        print("Member not found or error occurred.")
        return
    old = res[0]
    print(f"Current Name: {old[1]} | JoinDate: {old[2]} | Type: {old[3]} | Mentor: {old[4]}")
    name = input("New Name (press Enter to keep): ") or old[1]
    joindate = input("New JoinDate (YYYY-MM-DD) (Enter to keep): ") or old[2]
    mtype = input("New Type (Student/Faculty/Staff) (Enter to keep): ") or old[3]
    mentor = input("New Mentor MID (Enter to keep / blank for NULL): ")
    mentor_val = mentor if mentor.strip() != "" else None
    sql = "UPDATE LAB_MEMBER SET Name=%s, JoinDate=%s, MType=%s, Mentor=%s WHERE MID=%s"
    if execute_query(conn, sql, (name, joindate, mtype, mentor_val, mid)):
        print("✅ Member updated.")

def update_project(conn):
    pid = input("Enter Project ID to update: ")
    res = execute_query(conn, "SELECT PID, Title, SDate, EDate, Leader FROM PROJECT WHERE PID=%s", (pid,), is_select=True)
    if not res:
        print("Project not found or error occurred.")
        return
    old = res[0]
    print(f"Current Title: {old[1]} | SDate: {old[2]} | EDate: {old[3]} | Leader: {old[4]}")
    title = input("New Title (Enter to keep): ") or old[1]
    sdate = input("New Start Date (YYYY-MM-DD) (Enter to keep): ") or old[2]
    edate = input("New End Date (YYYY-MM-DD) (Enter to keep / blank for NULL): ")
    edate_val = edate if edate.strip() != "" else None
    leader = input("New Leader MID (Enter to keep / blank for NULL): ")
    leader_val = leader if leader.strip() != "" else None
    sql = "UPDATE PROJECT SET Title=%s, SDate=%s, EDate=%s, Leader=%s WHERE PID=%s"
    if execute_query(conn, sql, (title, sdate, edate_val, leader_val, pid)):
        print("✅ Project updated.")

# ----------------------------
# CLI: USES (Equipment Usage) CRUD
# ----------------------------
def add_usage(conn):
    print("Add new equipment usage record:")
    mid = input("Member ID (MID): ")
    eid = input("Equipment ID (EID): ")
    sdate = input("Start Date (YYYY-MM-DD): ")
    edate = input("End Date (YYYY-MM-DD): ")
    sql = "INSERT INTO USES (MID, EID, SDate, EDate) VALUES (%s, %s, %s, %s)"
    if execute_query(conn, sql, (mid, eid, sdate, edate)):
        print("✅ Usage added.")

def update_usage(conn):
    print("Update an equipment usage record (primary key: MID, EID, SDate).")
    mid = input("Member ID (MID): ")
    eid = input("Equipment ID (EID): ")
    sdate = input("Original Start Date (YYYY-MM-DD): ")
    res = execute_query(conn, "SELECT MID, EID, SDate, EDate FROM USES WHERE MID=%s AND EID=%s AND SDate=%s", (mid, eid, sdate), is_select=True)
    if not res:
        print("Usage record not found.")
        return
    old = res[0]
    print(f"Current EDate: {old[3]}")
    new_sdate = input("New Start Date (Enter to keep): ") or old[2]
    new_edate = input("New End Date (Enter to keep): ") or old[3]
    # handle PK change case: delete old and insert new if start date changed
    if new_sdate != old[2]:
        # delete old, then insert new
        execute_query(conn, "DELETE FROM USES WHERE MID=%s AND EID=%s AND SDate=%s", (mid, eid, sdate))
        sql = "INSERT INTO USES (MID, EID, SDate, EDate) VALUES (%s, %s, %s, %s)"
        if execute_query(conn, sql, (mid, eid, new_sdate, new_edate)):
            print("✅ Usage updated (PK changed).")
    else:
        sql = "UPDATE USES SET EDate=%s WHERE MID=%s AND EID=%s AND SDate=%s"
        if execute_query(conn, sql, (new_edate, mid, eid, sdate)):
            print("✅ Usage updated.")

def remove_usage(conn):
    print("Delete an equipment usage record.")
    mid = input("Member ID (MID): ")
    eid = input("Equipment ID (EID): ")
    sdate = input("Start Date (YYYY-MM-DD): ")
    sql = "DELETE FROM USES WHERE MID=%s AND EID=%s AND SDate=%s"
    if execute_query(conn, sql, (mid, eid, sdate)):
        print("✅ Usage deleted.")

# ==========================================
# MENU 1: PROJECT & MEMBER MANAGEMENT
# (modified to let DB generate IDs for members/projects/equipment)
# ==========================================
def menu_projects_members(conn):
    while True:
        clear_screen()
        print("\n--- 📁 PROJECT & MEMBER MANAGEMENT ---")
        print("1. Add New Member")
        print("2. Remove Member")
        print("3. Update Member")
        print("4. Add New Project")
        print("5. Update Project")
        print("6. Check Project Status")
        print("7. Report: Mentorship Relations in Projects")
        print("8. Report: Members working on Grant-Funded Projects")
        print("9. Back to Main Menu")
        c = input("Select: ").strip()

        if c == '1':
            # NEW: do not ask for MID (AUTO_INCREMENT will create it)
            name = input("Name: ").strip()
            date = input("Join Date (YYYY-MM-DD): ").strip()
            mtype = input("Type (Student/Faculty/Staff) [Student]: ").strip() or "Student"
            mentor = input("Mentor MID (optional): ").strip()
            mentor_val = mentor if mentor != "" else None

            sql = "INSERT INTO LAB_MEMBER (Name, JoinDate, MType, Mentor) VALUES (%s, %s, %s, %s)"
            new_mid = execute_query(conn, sql, (name, date, mtype, mentor_val), return_lastrow=True)
            if new_mid is not None:
                print(f"✅ Member Added. Assigned MID = {new_mid}")
            else:
                print("⚠️ Failed to add member.")

        elif c == '2':
            mid = input("Member ID to Delete: ").strip()
            if execute_query(conn, "DELETE FROM LAB_MEMBER WHERE MID = %s", (mid,)):
                print("✅ Member Deleted.")

        elif c == '3':
            update_member(conn)

        elif c == '4':
            # NEW: do not ask for PID (AUTO_INCREMENT will create it)
            title = input("Title: ").strip()
            sdate = input("Start Date (YYYY-MM-DD): ").strip()
            edate = input("End Date (YYYY-MM-DD) (optional): ").strip() or None
            duration = input("Duration (months) (optional): ").strip() or None
            leader = input("Leader MID (optional): ").strip() or None

            sql = "INSERT INTO PROJECT (Title, SDate, EDate, EDuration, Leader) VALUES (%s, %s, %s, %s, %s)"
            new_pid = execute_query(conn, sql, (title, sdate, edate, duration, leader), return_lastrow=True)
            if new_pid is not None:
                print(f"✅ Project Created. Assigned PID = {new_pid}")
            else:
                print("⚠️ Failed to create project.")

        elif c == '5':
            update_project(conn)

        elif c == '6':
            # --- robust project status lookup ---
            raw = input("Enter Project ID: ").strip()
            if raw == "":
                print("⚠️  No Project ID entered.")
                input("Press Enter to continue...")
                continue

            cleaned = raw.rstrip(".,; ")
            try:
                pid_param = int(cleaned)
            except ValueError:
                print(Fore.RED + f"Invalid Project ID entered: {repr(raw)}. Please enter a numeric PID (e.g. 501).")
                input("Press Enter to continue...")
                continue

            res = execute_query(conn, "SELECT Title, SDate, EDate FROM PROJECT WHERE PID=%s", (pid_param,), is_select=True)
            if res is None:
                input("Press Enter to continue...")
                continue

            if len(res) == 0:
                print("⚠️ Project not found. Make sure the PID is correct (try 501, 502, ...).")
            else:
                title, sdate, edate = res[0]
                status = "Active" if edate is None else f"Ended {edate}"
                print(Fore.GREEN + f"ℹ️  {title} | Started: {sdate} | Status: {status}")

            input("Press Enter to continue...")

        elif c == '7':
            sql = """
            SELECT P.Title, Mentor.Name, Mentee.Name
            FROM WORKS W1
            JOIN WORKS W2 ON W1.PID = W2.PID
            JOIN LAB_MEMBER Mentee ON W1.MID = Mentee.MID
            JOIN LAB_MEMBER Mentor ON W2.MID = Mentor.MID
            JOIN PROJECT P ON W1.PID = P.PID
            WHERE Mentee.Mentor = Mentor.MID
            """
            res = execute_query(conn, sql, is_select=True)
            if res:
                for r in res: print(f"Project: {r[0]} | Mentor: {r[1]} -> Mentee: {r[2]}")
            else:
                print("No mentorship records found or error.")
            input("Press Enter to continue...")

        elif c == '8':
            gid = input("Enter Grant ID (e.g., 1001): ").strip()
            sql = """
            SELECT DISTINCT M.Name, P.Title
            FROM FUNDS F
            JOIN PROJECT P ON F.PID = P.PID
            JOIN WORKS W ON P.PID = W.PID
            JOIN LAB_MEMBER M ON W.MID = M.MID
            WHERE F.GID = %s
            """
            res = execute_query(conn, sql, (gid,), is_select=True)
            if res:
                for r in res: print(f"Member: {r[0]} (Project: {r[1]})")
            else:
                print("No records found for that grant or error.")
            input("Press Enter to continue...")

        elif c == '9':
            break
        else:
            print("Invalid option. Press Enter and try again.")
            input()

# ==========================================
# MENU 2: EQUIPMENT USAGE TRACKING
# (Add Equipment updated to let DB generate EID)
# ==========================================
def menu_equipment(conn):
    while True:
        clear_screen()
        print("\n--- 🛠️ EQUIPMENT TRACKING ---")
        print("1. Add New Equipment")
        print("2. Update Equipment Status")
        print("3. Show Active Users for Equipment")
        print("4. Add Equipment Usage")
        print("5. Update Equipment Usage")
        print("6. Remove Equipment Usage")
        print("7. Remove Equipment")
        print("8. Back to Main Menu")
        c = input("Select: ")

        if c == '1':
            # NEW: do not ask for EID
            name = input("Name: ").strip()
            etype = input("Type: ").strip()
            status = input("Status [Active]: ").strip() or "Active"
            pdate = input("Purchase/Provision Date (YYYY-MM-DD) (optional): ").strip() or None

            sql = "INSERT INTO EQUIPMENT (EType, EName, Status, PDate) VALUES (%s, %s, %s, %s)"
            new_eid = execute_query(conn, sql, (etype, name, status, pdate), return_lastrow=True)
            if new_eid is not None:
                print(f"✅ Equipment Added. Assigned EID = {new_eid}")
            else:
                print("⚠️ Failed to add equipment.")

        elif c == '2':
            eid = input("Equipment ID: ")
            stat = input("New Status (e.g., Maintenance): ")
            if execute_query(conn, "UPDATE EQUIPMENT SET Status=%s WHERE EID=%s", (stat, eid)):
                print("✅ Status Updated.")

        elif c == '3':
            eid = input("Equipment ID (Try 801): ")
            sql = """
            SELECT M.Name, P.Title
            FROM USES U
            JOIN LAB_MEMBER M ON U.MID = M.MID
            LEFT JOIN WORKS W ON M.MID = W.MID
            LEFT JOIN PROJECT P ON W.PID = P.PID
            WHERE U.EID = %s AND CURDATE() BETWEEN U.SDate AND U.EDate
            """
            res = execute_query(conn, sql, (eid,), is_select=True)
            if res:
                for r in res: print(f"User: {r[0]} | Project Context: {r[1]}")
            else:
                print("ℹ️  No active users right now.")

        elif c == '4':
            add_usage(conn)

        elif c == '5':
            update_usage(conn)

        elif c == '6':
            remove_usage(conn)

        elif c == '7':
            eid = input("Equipment ID to remove: ")
            sql_uses = "DELETE FROM USES WHERE EID = %s"
            execute_query(conn, sql_uses, (eid,))
            sql_eq = "DELETE FROM EQUIPMENT WHERE EID = %s"
            if execute_query(conn, sql_eq, (eid,)):
                print("✅ Equipment removed (and related usage records deleted).")
            else:
                print("⚠️ Failed to remove equipment (check ID).")

        elif c == '8':
            break

        else:
            print("Invalid option. Press Enter and try again.")
            input()

# ==========================================
# MENU 3: GRANT & PUBLICATION REPORTING
# ==========================================
def menu_reporting(conn):
    while True:
        print("\n--- 📊 REPORTS & ANALYTICS ---")
        print("1. Member with Highest Publications")
        print("2. Average Student Publications per Major")
        print("3. Top 3 Prolific Members for a Grant")
        print("4. Active Projects by Grant & Date Range")
        print("5. Back to Main Menu")
        c = input("Select: ")

        if c == '1':
            # Req: Identify member with highest number of publications
            sql = """
            SELECT M.Name, COUNT(PB.PID) as C 
            FROM LAB_MEMBER M JOIN PUBLISHES PB ON M.MID=PB.MID 
            GROUP BY M.MID ORDER BY C DESC LIMIT 1
            """
            res = execute_query(conn, sql, is_select=True)
            if res: print(f"🏆 Top Publisher: {res[0][0]} with {res[0][1]} publications.")
            else: print("No data or error.")

        elif c == '2':
            print("\n📈 Avg Publications per Major:")
            sql = """
            SELECT S.Major, COUNT(Pub.PID) / COUNT(DISTINCT S.MID)
            FROM STUDENT S JOIN PUBLISHES Pub ON S.MID=Pub.MID
            GROUP BY S.Major
            """
            res = execute_query(conn, sql, is_select=True)
            if res:
                for r in res: print(f"Major: {r[0]:<20} | Avg: {float(r[1]):.2f}")
            else:
                print("No data or error.")

        elif c == '3':
            gid = input("Enter Grant ID (e.g., 1001): ")
            sql = """
            SELECT M.Name, COUNT(Pub.PID) as Pubs
            FROM FUNDS F JOIN PROJECT P ON F.PID = P.PID
            JOIN WORKS W ON P.PID = W.PID JOIN LAB_MEMBER M ON W.MID = M.MID
            JOIN PUBLISHES Pub ON M.MID = Pub.MID
            WHERE F.GID = %s GROUP BY M.MID ORDER BY Pubs DESC LIMIT 3
            """
            res = execute_query(conn, sql, (gid,), is_select=True)
            if res:
                print(f"\nTop Contributors for Grant {gid}:")
                for r in res: print(f"{r[0]} ({r[1]} pubs)")
            else:
                print("No contributors found or error.")

        elif c == '4':
            gid = input("Enter Grant ID: ")
            start = input("Period Start (YYYY-MM-DD): ")
            end = input("Period End (YYYY-MM-DD): ")
            sql = """
            SELECT P.Title FROM FUNDS F JOIN PROJECT P ON F.PID = P.PID
            WHERE F.GID = %s AND (P.SDate <= %s AND P.EDate >= %s)
            """
            res = execute_query(conn, sql, (gid, end, start), is_select=True)
            if res:
                print(f"Active Projects in that period: {[r[0] for r in res]}")
            else:
                print("No active projects found in that range or error.")

        elif c == '5':
            break

# ==========================================
# MAIN APPLICATION LOOP
# ==========================================
def main():
    conn = create_connection()
    if not conn:
        print(Fore.RED + "Could not connect to database. Exiting.")
        return

    while True:
        clear_screen()
        print(Fore.CYAN + "=" * 50)
        print(Fore.YELLOW + "🔬 RESEARCH LAB MANAGER (MAIN MENU)".center(50))
        print(Fore.CYAN + "=" * 50 + Style.RESET_ALL)

        print(Fore.GREEN + "1. Project and Member Management")
        print("2. Equipment Usage Tracking")
        print("3. Grant and Publication Reporting")
        print(Fore.RED + "4. Exit Application" + Style.RESET_ALL)

        choice = input(Fore.CYAN + "\nEnter Choice (1-4): " + Style.RESET_ALL)

        if choice == '1':
            menu_projects_members(conn)
        elif choice == '2':
            menu_equipment(conn)
        elif choice == '3':
            menu_reporting(conn)
        elif choice == '4':
            print(Fore.YELLOW + "Exiting... Bye! 👋")
            break
        else:
            print(Fore.RED + "Invalid choice. Press Enter and try again.")
            input()

    conn.close()

if __name__ == "__main__":
    main()