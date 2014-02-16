#Copyright (c) 2014 David Harwood

#Licensed under the terms of the MIT license
#http://opensource.org/licenses/MIT

#Twisted imports
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc

#system imports
import time, sys, argparse, csv, re
from ConfigParser import RawConfigParser

class AchievementHandler:
    """
    The class that handles the actual achievements, who gets them, who doesn't, etc.
    """

    achievefile = 'achievements'
    userfile = 'users'

    def __init__(self, config):
        #TODO: read config file, make settings changes as needed
        #more will be added here when there are acutally some options defined
        pass

    def command(self, user, channel, msg):
        parse = msg.split(None, 1)
        if parse[0] == 'grant':
            granter = parse[1].split(None, 1)
            return self.grant(granter[0], self._titlecase(granter[1]))
        elif parse[0] == 'earned':
            return self.earned(parse[1])
        elif parse[0] == 'add':
            return self.add_achievement(parse[1])
        elif parse[0] == 'list':
            return self.list_achievements()
        elif parse[0] == 'info':
            return self.info(self._titlecase(parse[1]))
        elif parse[0] == 'help':
            return self.help_info()
        else:
            return "Command %s not found" % (parse[0])

    def _titlecase(self, s):
        return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)

    def _achexists(self, achievement):
        exists = False
        for line in open(self.achievefile, 'r'):
            if line.partition(' : ')[0] == achievement:
                exists = True
                break
        return exists

    def grant(self, user, achievement):
        if not self._achexists(achievement):
            return 'Achievement not found!'
        with open(self.userfile, 'a') as record:
            record.write('%s -> %s\n' % (user, achievement))
            record.flush()
        return 'Achievement unlocked! %s has earned the achievement %s!' % (user, achievement)

    def earned(self, user):
        earned = ', '.join([ line.strip().split(None, 2)[2] for line in open(self.userfile, 'r') if line.split()[0] == user ])
        return '%s has earned %s' % (user, earned)

    def add_achievement(self, achieve_block):
        parts = achieve_block.split(' : ')
        if len(parts) < 2:
            return 'Achievement not added (I need at least a name and a description, more info optional)'
        parts[0] = self._titlecase(parts[0])
        if self._achexists(parts[0]):
            return 'Achievement not added: achievement with that name already exists!'
        with open(self.achievefile, 'a') as achievements:
            achievements.write(' : '.join(parts) + '\n')
            achievements.flush()
        return 'Added new achievement: %s' % (parts[0])

    def list_achievements(self):
        achievements = ', '.join([ line.split(' : ', 1)[0] for line in open(self.achievefile, 'r') ])
        return 'List of achievements: %s' % (achievements)

    def info(self, achievement):
        for line in open(self.achievefile, 'r'):
            if line.partition(' : ')[0] == achievement:
                parts = line.strip().split(' : ')
                if len(parts) == 2:
                    return '%s: %s' % (parts[0], parts[1])
                else:
                    return '%s: %s (%s)' % (parts[0], parts[1], parts[2])
        return 'Achievement not found!'

    def help_info(self):
        script = ['I am Achievebot, made to track IRC achievements',
                'Commands:',
                'grant <user> <achievement> -> Grant achievement to user',
                'earned <user> -> Display all of the achievements the user has earned',
                'list -> List all available achievements',
                'add <name> : <description> : <how to earn> -> Add a new achievement to the system (<how to earn> is optional)',
                'info <achievement> -> Show the full block of info on the specified achievement',
                'help -> Display this help',
                'join <channel> -> Join the specified channel',
                'leave <channel> -> Leave the specified channel',
                'quit -> Quit IRC',
                'More information and source code can be found at https://github.com/dharwood/Achievebot']
        return '\n'.join(script)

class AchieveBot(irc.IRCClient):
    """
    An IRC bot to grant and keep track of achievements users earn.
    """

    nickname = "achievebot"
    lineRate = 0.2

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.achieve = AchievementHandler(self.factory.appopts)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if channel == self.nickname:
            self.command(user, user, msg)
        elif msg.startswith(self.nickname):
            self.command(user, channel, msg.split(None, 1)[1])

    def command(self, user, channel, msg):
        if msg.startswith("quit"):
            self.quit(message="I have been told to leave")
        elif msg.startswith("join"):
            parts = msg.split()
            if len(parts) > 2:
                self.join(parts[1], key=parts[2])
            else:
                self.join(msg.split()[1])
        elif msg.startswith("leave"):
            self.leave(msg.split()[1], reason="I've been told to part")
        else:
            self.msg(channel, self.achieve.command(user, channel, msg))

class AchieveBotFactory(protocol.ClientFactory):
    """
    A factory for AchieveBots.
    """

    protocol = AchieveBot

    def __init__(self, config, ircopts, appopts):
        self.config = config
        self.ircopts = ircopts
        self.appopts = appopts

    def clientConnectionLost(self, connector, reason):
        reactor.stop()
        #reconnect if connection lost
        #connector.connect()


    def clientConnectionFailed(self, connector, reason):
        reactor.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bot for IRC achievements')
    parser.add_argument('-c', '--config', default='abot.conf', metavar='FILE', help='Config file to use. If it is missing, a default configuration file will be generated at the same path.')
    parser.add_argument('-s', '--server', help='Server to connect to (overrides config file)')
    parser.add_argument('-p', '--port', type=int, help='Port to connect to (overrides config file)')
    parser.add_argument('--ssl', action='store_true', help='Connect using SSL (overrides config file)')
    args = parser.parse_args()

    conf = RawConfigParser()
    try:
        conf.read(args.config)
        serv = conf.get('Connection', 'server')
        port = conf.getint('Connection', 'port')
        usessl = conf.getboolean('Connection', 'usessl')
    except:
        print("Configuration file can't be read. Generating.")
        conf.add_section('Connection')
        conf.set('Connection', 'server', 'INSERT VALUE HERE')
        conf.set('Connection', 'port', '6667')
        conf.set('Connection', 'usessl', 'no')
        conf.add_section('IRC Options')
        conf.add_section('Achievement Options')
        conf.write(open(args.config, 'wb'))
        print("Add IRC server address before using.")
        sys.exit()

    if args.server is not None:
        serv = args.server
    if args.port is not None:
        port = args.port
    if args.ssl:
        usessl = True

    f = AchieveBotFactory(args.config, dict(conf.items('IRC Options')), dict(conf.items('Achievement Options')))
    if usessl:
        reactor.connectSSL(serv, port, f, ssl.CertificateOptions())
    else:
        reactor.connectTCP(serv, port, f)
    reactor.run()

