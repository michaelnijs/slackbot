

command_to_trigger = "say"
command_help = "Make the bot say something"
command_required_admin = False

parentobj = None

def initModule(parent):
    global parentobj
    parentobj = parent
    print "Nothing to do"


def handle_command(command, channel, callfrom):
    parts = command.split(' ')
    if len(parts) < 2:
        response = "Say what?"
    else:
        response = ' '.join(parts[1:]).replace("You are","I'm").replace("you are","I am").replace("You","I").replace("you","I")
    return response
