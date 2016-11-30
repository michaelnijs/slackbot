from slackclient import SlackClient


BOT_NAME = "seccy"
SLACK_BOT_TOKEN = ""

slack_client = SlackClient(SLACK_BOT_TOKEN)

if __name__ == "__main__":

    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print "Bot ID: " + user.get('id')
            if 'name' in user:
                print user.get('name')
