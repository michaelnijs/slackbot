
import sqlite3
import time

command_to_trigger = "feature"
command_help = "Propose a feature request. The admins could use this to give me new intelligence."
command_required_admin = False

parentobj = None

def initModule(parent):
    global parentobj
    parentobj = parent
    print "Nothing to do"

    con = parentobj.getDBConnection()
    cur = con.cursor()

    try:
        cur.execute("SELECT id from slackbot_features")
    except sqlite3.OperationalError:
        # Table does not exist, we create it!
        sql = "CREATE TABLE slackbot_features (id integer primary key autoincrement, feature text, userid integer, addeddate text, completed boolean)"
        cur.execute(sql)
        con.commit()

    parentobj.closeDBConnection(con)


def handle_command(command, channel, callfrom):
    parts = command.split(' ')
    if parts[1] == "showallrequestedfeatures":
        con = parentobj.getDBConnection()
        cur = con.cursor()

        sql = "select feature from slackbot_features where completed = 0"
        cur.execute(sql)
        response = ""
        for item in cur.fetchall():
            response = response + item[0] + "\n"

    else:
        con = parentobj.getDBConnection()
        cur = con.cursor()

        feature = ' '.join(parts[1:])
        sql = "SELECT id from slackbot_knownusers WHERE userid = ? or username = ?"
        data = (callfrom, callfrom)

        cur.execute(sql, data)
        userid = cur.fetchone()[0]

        sql = "INSERT INTO slackbot_features (feature, userid, addeddate, completed) VALUES (?,?,?,0)"
        data = (feature, userid, str(int(time.time())))

        cur.execute(sql, data)

        parentobj.closeDBConnection(con)
        
        response = "Feature request added"
    return response
