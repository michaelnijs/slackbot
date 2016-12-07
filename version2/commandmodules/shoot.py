
from random import randint

command_to_trigger = "shoot"
command_help = "Play a game of russian roulette. Will automatically reload upon hit."
command_required_admin = False

parentobj = None

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

def initModule(parent):
    global parentobj
    parentobj = parent
    reset_roulette_game()


def handle_command(command, channel, callfrom):
    ret = shoot()
    if ret == 1:
        con = parentobj.getDBConnection()
        cur = con.cursor()

        sqlquery = "select username from slackbot_knownusers WHERE userid = ?"
        data = (callfrom,)
        cur.execute(sqlquery, data)


        response = cur.fetchone()[0] + " just died with a bullet splicing his head"

        parentobj.closeDBConnectionNoCommit(con)
        reset_roulette_game()
    else:
        response = "*click*"

    return response
