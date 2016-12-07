

command_to_trigger = "bio"
command_help = "The bio feature allows you to fetch the bio of people and set your own. use 'bio help' for more info."
command_required_admin = False

parentobj = None

def initModule(parent):
    global parentobj
    parentobj = parent
    print "Nothing to do"


def handle_command(command, channel, callfrom):
    parts = command.split(' ')
    if parts[1] == "help":
        response = '''
The bio help page
- bio <ATusername>
    Will load the bio of that person
- bio add <free text>
    Will set your bio to the text provided. No need for brackets, just write.
'''

    elif parts[1] == "add":
        bio = ' '.join(parts[2:])
        try:
            con = parentobj.getDBConnection()
            cur = con.cursor()

            sqlquery = "SELECT id from slackbot_knownusers WHERE userid LIKE ? or username LIKE ?"
            data = (callfrom, callfrom)

            cur.execute(sqlquery, data)

            id = cur.fetchone()[0]
            print bio
            parentobj.closeDBConnection(con)
            con = parentobj.getDBConnection()
            cur = con.cursor()

            # find if a bio exists

            sqlquery = "SELECT id from slackbot_bio WHERE userid = ?"
            data = (id,)
            cur.execute(sqlquery, data)

            res = cur.fetchone()

            print res

            if res == [] or res == None:
                print "Inserting it!"
                sqlquery = "INSERT INTO slackbot_bio (userid, bio) VALUES (?,?)"
                data = (id, bio)
                cur = con.cursor()
                cur.execute(sqlquery, data)
                con.commit()
                response = "Bio added"
            else:
                sqlquery = "UPDATE slackbot_bio SET bio = ? where id = ?"
                data = (bio, res[0])
                cur.execute(sqlquery, data)
                con.commit()
                response = "Bio updated"


            parentobj.closeDBConnection(con)

        except:
            response = "Failure!"
    else:
        username_to_add = parts[1]
        userid_given = False
        if parts[1].startswith('<'):
            # this is a userid
            userid_given = True
            username_to_add = username_to_add.replace('<@','').replace('>','').upper()

        # get the correct bio and respond it
        con = parentobj.getDBConnection()
        cur = con.cursor()

        if userid_given:
            sqlquery = "SELECT bio from slackbot_bio as sb left join slackbot_knownusers as sk on sb.userid = sk.id WHERE sk.userid like ?"
        else:
            sqlquery = "SELECT bio from slackbot_bio as sb left join slackbot_knownusers as sk on sb.userid = sk.id WHERE sk.username like ?"

        data = (username_to_add,)

        cur.execute(sqlquery, data)
        try:
            response = cur.fetchone()[0]
        except:
            response = "No bio set yet. Inform the user"

        parentobj.closeDBConnection(con)

    return response
