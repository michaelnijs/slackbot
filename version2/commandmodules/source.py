

command_to_trigger = "source"
command_help = "Who is the bot?"
command_required_admin = False

parentobj = None

def initModule(parent):
    global parentobj
    parentobj = parent
    print "Nothing to do"


def handle_command(command, channel, callfrom):
    response = "I'm a slackbot for Infosec belgium, source can be found on github https://github.com/michaelnijs/slackbot"
    return response
