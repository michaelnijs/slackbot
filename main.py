from slackclient import SlackClient
import time
import sys

import psycopg2
from random import randint

import opml
import feedparser

database_name = ""
database_username = ""

BOT_ID = ""
BOT_NAME = "seccy"
SLACK_BOT_TOKEN = ""

AT_BOT = "<@" + BOT_ID + ">"


slack_client = SlackClient(SLACK_BOT_TOKEN)

owners = []
owners_name = []


roulette_hit_bullet = 0
roulette_shot_list = []
roulette_number_of_bullets = 6
roulette_score = {}

def reset_roulette_game(bullets = 6):
    global roulette_hit_bullet
    roulette_hit_bullet = randint(0, bullets-1)
    global roulette_shot_list
    roulette_shot_list = []
    global roulette_number_of_bullets
    roulette_number_of_bullets = bullets

def shoot():
    validshot = False
    shot = None
    while not validshot:
        shot = randint(0, roulette_number_of_bullets)

        if shot not in roulette_shot_list:
            validshot = True

    if shot == roulette_hit_bullet:
        return 1
    else:
        roulette_shot_list.append(shot)
        return 0

def load_owners():

    global owners
    owners = []
    global owners_name
    owners_name = []

    con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
    cur = con.cursor()

    cur.execute("SELECT userid, username from slackbot_owners")

    for owner in cur.fetchall():
        owners.append(owner[0])
        owners_name.append(owner[1])

def load_users():

    con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
    cur = con.cursor()

    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user:
                id = None
                try:
                    sql = "SELECT id from slackbot_knownusers WHERE username LIKE %s and userid LIKE %s"
                    data = (user.get('name'), user.get('id'))

                    cur.execute(sql, data)
                    id = cur.fetchone()[0]

                    # update row
                    sql = "UPDATE slackbot_knownusers SET lastseen = %s WHERE username LIKE %s and userid LIKE %s"
                    data = (str(int(time.time())), user.get('name'), user.get('id'))
                    cur.execute(sql, data)
                except:
                    # new user
                    sql = "INSERT INTO slackbot_knownusers (username, userid, lastseen) VALUES (%s,%s,%s)"
                    data = (user.get('name'), user.get('id'), str(int(time.time())))
                    send_welcome_message()
                    cur.execute(sql,data)

            con.commit()

def reload_news(feedid):

    con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
    cur = con.cursor()

    sqlquery = "SELECT xmlUrl from slackbot_feeds WHERE id = %s and borked = false"
    data = (feedid,)

    url = ""
    try:
        cur.execute(sqlquery, data)
        url = cur.fetchone()[0]
    except:
        return -1

    d = feedparser.parse(url)

    if len(d.entries) == 0:
        # something is borked, mark it as such
        sqlquery = "UPDATE slackbot_feeds SET borked = true where id = %s"
        data = (feedid,)
        cur.execute(sqlquery, data)
        con.commit()
        return -1

    for i in range(len(d.entries)-1, 0):

        news_title = d.entries[i].title
        news_description = d.entries[i].description
        news_link = d.entries[i].link
        try:
            news_publishdate = d.entries[i].published
        except:
            news_publishdate = ""

        sqlquery = "SELECT id from slackbot_feed_content WHERE title LIKE % s and feedid = %s and description like %s and link like %s and publish_date like %s"
        data = (news_title, feedid, news_description, news_link, news_publishdate)
        try:
            cur.execute(sqlquery, data)
            id = cur.fetchone()[0]
        except:
            # adding it
            sqlquery = "INSERT INTO slackbot_feed_content (title, feedid, description, link, publish_date) VALUES (%s,%s,%s,%s,%s)"
            data = (news_title, feedid, news_description, news_link, news_publishdate)
            cur.execute(sqlquery, data)
            con.commit()

def load_rss_feeds():

    file_to_load = "security.opml"
    outline = opml.parse(file_to_load)

    # upload the feed in the database, verify if the feed is still the same and update if needed.
    con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
    cur = con.cursor()
    for i in range(0, len(outline)-1):
        feed_title = outline[i].title
        feed_xmlurl = outline[i].xmlUrl
        feed_htmlurl = outline[i].htmlUrl
        feed_type = outline[i].type

        try:
            sqlquery = "SELECT id from slackbot_feeds WHERE title LIKE %s and type LIKE %s and xmlurl LIKE %s and htmlurl LIKE %s"
            data = (feed_title, feed_type, feed_xmlurl, feed_htmlurl)
            cur.execute(sqlquery, data)
            id = cur.fetchone()[0]
        except:
            sqlquery = "INSERT INTO slackbot_feeds (title, type, xmlurl, htmlurl, borked) VALUES (%s,%s,%s,%s,%s)"
            data = (feed_title, feed_type, feed_xmlurl, feed_htmlurl, "false")
            cur.execute(sqlquery, data)
            con.commit()

    con.close()

def send_welcome_message():

    #slack_client.api_call("chat.postMessage",channel=channel, text=response, as_user=True)
    return

def handle_command(command, channel, callfrom):
    response = ""

    if command.startswith("do"):
        response = "For now I do absolutely nothing..."
    elif command.startswith("quit"):

        if callfrom in owners:
            response = "I hear you master, see ya!"
            slack_client.api_call("chat.postMessage",channel=channel, text=response, as_user=True)
            print dir(slack_client)
            sys.exit()
        else:
            response = "Why should I listen to you??!! Go away"

    elif command.startswith("add"):
        parts = command.split(' ')
        if parts[1] == "admin":
            username_to_add = parts[2]
            userid_given = False
            if username_to_add.startswith('<'):
                # this is a userid
                userid_given = True
                username_to_add = username_to_add.replace('<@','').replace('>','').upper()
            try:
                con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
                cur = con.cursor()
                if not userid_given:
                    sql = "SELECT userid from slackbot_knownusers WHERE username LIKE %s"
                    data = (username_to_add, )
                    cur.execute(sql, data)

                    userid = cur.fetchone()[0]
                    username = username_to_add
                else:
                    sql = "SELECT username from slackbot_knownusers WHERE userid LIKE %s"
                    data = (username_to_add,)
                    cur.execute(sql, data)

                    username = cur.fetchone()[0]
                    userid = username_to_add

                sql = "INSERT INTO slackbot_owners (username, userid) VALUES (%s,%s)"
                data = (username, userid)

                cur.execute(sql, data)
                con.commit()

                load_owners()
                response = "Welcome to the new overlord " + username
                con.close()
            except:
                response = "Something barfed. Is the username correct?"

        elif parts[1] == "bio":
            bio = ' '.join(parts[2:])
            try:
                con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
                cur = con.cursor()

                sqlquery = "SELECT id from slackbot_knownusers WHERE userid LIKE %s or username LIKE %s"
                data = (callfrom, callfrom)

                cur.execute(sqlquery, data)

                id = cur.fetchone()[0]
                print bio
                con.close()
                con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
                cur = con.cursor()

                # find if a bio exists

                sqlquery = "SELECT id from slackbot_bio WHERE userid = %s"
                data = (id,)
                cur.execute(sqlquery, data)

                res = cur.fetchone()

                print res

                if res == [] or res == None:
                    print "Inserting it!"
                    sqlquery = "INSERT INTO slackbot_bio (userid, bio) VALUES (%s,%s)"
                    data = (id, bio)
                    cur = con.cursor()
                    cur.execute(sqlquery, data)
                    con.commit()
                    response = "Bio added"
                else:
                    sqlquery = "UPDATE slackbot_bio SET bio = %s where id = %s"
                    data = (bio, res[0])
                    cur.execute(sqlquery, data)
                    con.commit()
                    response = "Bio updated"


                con.close()

            except:
                response = "Failure!"


    elif command.startswith("remove"):
        parts = command.split(' ')
        if parts[1] == "admin":
            username_to_remove = parts[2]
            userid_given = False
            if username_to_remove.startswith('<'):
                # this is a userid

                userid_given = True
                username_to_remove = username_to_remove.replace('<@','').replace('>','').upper()
            try:
                con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
                cur = con.cursor()
                if not userid_given:
                    sql = "SELECT userid from slackbot_knownusers WHERE username LIKE %s"
                    data = (username_to_remove, )
                    cur.execute(sql, data)

                    userid = cur.fetchone()[0]
                    username = username_to_remove
                else:
                    sql = "SELECT username from slackbot_knownusers WHERE userid LIKE %s"
                    data = (username_to_remove,)
                    cur.execute(sql, data)

                    username = cur.fetchone()[0]
                    userid = username_to_remove

                sql = "DELETE FROM slackbot_owners WHERE username LIKE %s AND userid LIKE %s"
                data = (username, userid)


                cur.execute(sql, data)
                con.commit()

                load_owners()
                response = "Byebye! " + username + " is gone!"
                con.close()
            except:
                response = "Something barfed. Is the username correct?"
    elif command.startswith("list"):
        parts = command.split(' ')
        if parts[1] == "admins":
            response = "I'm enslaved by: \n"
            print owners_name
            for i in owners_name:
                response = response + i + "\n"

    elif command.startswith("!shoot"):
        ret = shoot()
        if ret == 1:
            con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
            cur = con.cursor()

            sqlquery = "select username from slackbot_knownusers WHERE userid = %s"
            data = (callfrom,)
            cur.execute(sqlquery, data)


            response = cur.fetchone()[0] + " just died with a bullet splicing his head"
        else:
            response = "*click*"

    elif command.startswith("!reload"):
        reset_roulette_game()
        response = "My gun is reloaded, want a piece of this? ... punk!"
    elif command.startswith("say"):
        parts = command.split(' ')
        if len(parts) < 2:
            response = "Say what?"
        else:
            response = ' '.join(parts[1:]).replace("You are","I'm").replace("you are","I am").replace("You","I").replace("you","I")

    elif command.startswith("lastseen"):
        parts = command.split(' ')
        if parts[1].startswith('<@'):
            con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
            cur = con.cursor()

            sql = "SELECT lastseen from slackbot_knownusers WHERE userid LIKE %s"
            data = (parts[1].replace("<@","").replace(">","").upper(),)

            cur.execute(sql, data)
            lastseen = cur.fetchone()[0]
            con.close()
        else:
            con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
            cur = con.cursor()

            sql = "SELECT lastseen from slackbot_knownusers WHERE username LIKE %s"
            data = (parts[1],)

            cur.execute(sql, data)
            lastseen = cur.fetchone()[0]
            con.close()

        response = "Last record: " + time.strftime("%d-%m-%Y %H:%M", time.localtime(int(lastseen)))

    elif command.startswith("reloadrss"):
        if callfrom in owners:
            load_rss_feeds()
            response = "done master!"
        else:
            response = "You want me to do what now?"

    elif command.startswith("reloadallnews"):
        if callfrom in owners:
            con = psycopg2.connect("dbname='%s' user='%s'"% (database_name, database_username))
            cur = con.cursor()

            cur.execute("SELECT Max(id) from slackbot_feeds")
            upper_bound = cur.fetchone()[0]
            for i in range(1, upper_bound):
                print "Fetching " + str(i)
                reload_news(i)

            response = "That took a while, do not do that too often"

    elif command.startswith("reloadnews"):
        if callfrom in owners:
            parts = command.split(' ')
            ret = reload_news(parts[1])
            if ret == -1:
                response = "Something is wrong with the feed, disabling it"
            else:
                response = "Data loaded for that feed"
        else:
            response = "how about no??"

    elif command.startswith("news"):
        con = psycopg2.connect("dbname='%s' user='%s'"% (database_name, database_username))
        cur = con.cursor()
        parts = command.split(" ")
        if parts[1] == "list":
            sqlquery = ("SELECT id, title from slackbot_feeds WHERE borked = false")
            data = ()
            cur.execute(sqlquery)

            for item in cur.fetchall():
                response = response + "\t" + str(item[0]) + " - " + str(item[1]) + "\n"

        else:
            try:
                id = int(parts[1])

                if isinstance(id, int) and id > 0:
                    sqlquery = "SELECT title, description, link, publish_date from slackbot_feed_content WHERE feedid = %s ORDER BY id ASC LIMIT 5"
                    data = (id,)
                    cur.execute(sqlquery, data)
                    for item in cur.fetchall():
                        response = response + "*" + str(item[0]) + "* - " + str(item[3]) + "\n" + str(item[1] + "\n" + str(item[2])) + "\n"
                else:
                    response = "You should read the help page more often"
            except:
                response = "Something went wrong..."
        con.close()

    elif command.startswith("bio"):
        parts = command.split(" ")
        username_to_add = parts[1]
        userid_given = False
        if parts[1].startswith('<'):
            # this is a userid
            userid_given = True
            username_to_add = username_to_add.replace('<@','').replace('>','').upper()



        # get the correct bio and respond it
        con = psycopg2.connect("dbname='%s' user='%s'" % (database_name, database_username))
        cur = con.cursor()

        if userid_given:
            sqlquery = "SELECT bio from slackbot_bio as sb left join slackbot_knownusers as sk on sb.userid = sk.id WHERE sk.userid like %s"
        else:
            sqlquery = "SELECT bio from slackbot_bio as sb left join slackbot_knownusers as sk on sb.userid = sk.id WHERE sk.username like %s"

        data = (username_to_add,)

        cur.execute(sqlquery, data)
        try:
            response = cur.fetchone()[0]
        except:
            response = "No bio set yet. Inform the user"

    elif command.startswith("help"):
        response = """Still a work in progress. For now we have:
        - do
        - quit
        - help
        - !shoot
        - !reload
        - news list
        - news <title>
        - bio <username>
        - add bio <your bio here>
        - I have more hidden commands...
        """

    slack_client.api_call("chat.postMessage",channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):


    # some fix is required here to prevent blalbalba @bot blalba to respond TODO
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output["text"]:
                return output['text'].split(AT_BOT)[1].strip().lower(), output['channel'], output['user']

    return None, None, None



if __name__ == "__main__":

    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print "Connected"

        load_owners()
        load_users()
        reset_roulette_game()
        load_rss_feeds()
        while True:
            command, channel, callfrom = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, callfrom)

            load_users()
            time.sleep (READ_WEBSOCKET_DELAY)
    else:
        print "Something barfed"
