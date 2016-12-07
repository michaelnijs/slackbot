#!/usr/bin/python
 # -*- coding: utf-8 -*-


import opml
import feedparser

command_to_trigger = "news"
command_help = "This is the news module, use 'news help' for more information"
command_required_admin = False

parentobj = None

def initModule(parent):
    global parentobj
    parentobj = parent
    print "Nothing to do"

def reload_news(feedid):

    con = parentobj.getDBConnection()
    cur = con.cursor()

    sqlquery = "SELECT xmlUrl from slackbot_feeds WHERE id = ? and borked = 'false'"
    data = (feedid,)

    url = ""

    print "Loading news for item: " + str(feedid)
    try:
        cur.execute(sqlquery, data)
        url = cur.fetchone()[0]
    except:
        return -1

    d = feedparser.parse(url)

    if len(d.entries) == 0:
        # something is borked, mark it as such
        sqlquery = "UPDATE slackbot_feeds SET borked = 'true' where id = ?"
        data = (feedid,)
        cur.execute(sqlquery, data)
        con.commit()
        print "Not ok!!"
        return -1

    print "We have entries"


    for i in range(len(d.entries)-1, 0, -1):
        print "Fetching item: " + str(i)
        news_title = d.entries[i].title
        news_description = d.entries[i].description
        news_link = d.entries[i].link
        try:
            news_publishdate = d.entries[i].published
        except:
            news_publishdate = ""



        sqlquery = "SELECT id from slackbot_feed_content WHERE title LIKE ? and feedid = ? and description like ? and link like ? and publish_date like ?"
        data = (news_title, feedid, news_description, news_link, news_publishdate)
        try:

            cur.execute(sqlquery, data)
            id = cur.fetchone()[0]
            print "The news exists"
        except:
            # adding it
            print "Adding news"
            sqlquery = "INSERT INTO slackbot_feed_content (title, feedid, description, link, publish_date) VALUES (?,?,?,?,?)"
            data = (news_title, feedid, news_description, news_link, news_publishdate)
            cur.execute(sqlquery, data)
            con.commit()

    print "End of the loop"
    parentobj.closeDBConnection(con)

def load_rss_feeds():

    file_to_load = "security.opml"
    outline = opml.parse(file_to_load)

    # upload the feed in the database, verify if the feed is still the same and update if needed.
    con = parentobj.getDBConnection()
    cur = con.cursor()
    for i in range(0, len(outline)-1):
        feed_title = outline[i].title
        feed_xmlurl = outline[i].xmlUrl
        feed_htmlurl = outline[i].htmlUrl
        feed_type = outline[i].type

        try:
            sqlquery = "SELECT id from slackbot_feeds WHERE title LIKE ? and type LIKE ? and xmlurl LIKE ? and htmlurl LIKE ?"
            data = (feed_title, feed_type, feed_xmlurl, feed_htmlurl)
            cur.execute(sqlquery, data)
            id = cur.fetchone()[0]
        except:
            sqlquery = "INSERT INTO slackbot_feeds (title, type, xmlurl, htmlurl, borked) VALUES (?,?,?,?,?)"
            data = (feed_title, feed_type, feed_xmlurl, feed_htmlurl, "false")
            cur.execute(sqlquery, data)
            con.commit()

    parentobj.closeDBConnection(con)

def handle_command(command, channel, callfrom):
    parts = command.split(' ')
    if parts[1] == "help":
        response = '''
Help for the news module:
- news list
    This will result in a list of news sources. Remember the number in front.
- news <id>
    Read the last 5 items for the news feed provided. The ID is the number from the list command
-* news reloadall
-* news reloadrss
'''

    elif parts[1] == "reloadrss":
        if callfrom in parentobj.getOwners():
            load_rss_feeds()
            response = "The feed is reloaded"
        else:
            response = "Admin function, sorry"

    elif parts[1] == "reloadallnews":
        if callfrom in parentobj.getOwners():
            con = parentobj.getDBConnection()
            cur = con.cursor()

            cur.execute("SELECT Max(id) from slackbot_feeds")
            upper_bound = cur.fetchone()[0]
            for i in range(1, upper_bound):
                print "Fetching " + str(i)
                reload_news(i)

            response = "That took a while, do not do that too often"

            parentobj.closeDBConnection(con)

    elif parts[1] == "reloadnews":
        if callfrom in parentobj.getOwners():
            ret = reload_news(parts[2])
            if ret == -1:
                response = "Something is wrong with the feed, disabling it"
            else:
                response = "Data loaded for that feed"
        else:
            response = "how about no??"

    elif parts[1] == "list":
        con = parentobj.getDBConnection()
        cur = con.cursor()
        sqlquery = ("SELECT id, title from slackbot_feeds WHERE borked = 'false'")
        data = ()
        cur.execute(sqlquery)
        response = ""
        for item in cur.fetchall():

            response = response + "\t" + str(item[0]).replace(u'\u2248','') + " - " + str(item[1]).replace(u'\u2248','') + "\n"

    else:
        con = parentobj.getDBConnection()
        cur = con.cursor()
        response = ""
        #try:
        id = int(parts[1])
        if isinstance(id, int) and id > 0:
            print "fetching the news"
            sqlquery = "SELECT title, description, link, publish_date from slackbot_feed_content WHERE feedid = ? ORDER BY id ASC LIMIT 5"
            data = (id,)
            cur.execute(sqlquery, data)
            print "SQL executed"
            for item in cur.fetchall():
                print item
                response = response + "*" + str(item[0]) + "* - " + str(item[3]) + "\n" + str(item[1] + "\n" + str(item[2])) + "\n"
        else:
            response = "You should read the help page more often"
        #except:
        #    response = "Something went wrong..."

        parentobj.closeDBConnection(con)

    return response
