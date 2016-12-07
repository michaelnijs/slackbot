Slackbot version 2.0

A module needs some specific methods & variables. Just clone a module e.g. say.py and start from that. do not remove the following items:
- command_to_trigger
- command_help
- command_required_admin
- parentobj
- def initModule(parent)
- def handle_command(command, channel, callfrom)


From the parent the following methods can be invoked:
- setOwners(ownser), use with care
- getOwners(), if you have a subcommand that is for admins only
- closeDBConnection(con)
- closeDBConnectionNoCommit(con)
- getDBConnection()

For the database layout just see the sqlite file.
