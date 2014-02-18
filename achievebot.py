#Copyright (c) 2014 David Harwood

#Licensed under the terms of the MIT license
#http://opensource.org/licenses/MIT

#Twisted imports
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc

#system imports
import time, sys, argparse, re
from ConfigParser import RawConfigParser

class AchievementHandler:
    """
    The class that handles the actual achievements, who gets them, who doesn't, etc.
    """

    achievefile = 'achievements'
    userfile = 'users'
    admins = ''
    saynotice = 'grant_success'

    def __init__(self, config):
        for setting in config:
            setattr(self, setting[0], setting[1])

    def command(self, user, channel, msg):
        try:
            parse = msg.strip().split(None, 1)
            if len(parse) < 2:
                return getattr(self, parse[0])()
            else:
                return getattr(self, parse[0])(parse[1])
        except:
            return (self._saypick('command_fail'), 'What?') #command_fail

    def _achname(self, achievement):
        for line in open(self.achievefile, 'r'):
            if line.partition(' : ')[0].lower() == achievement.lower():
                return line.partition(' : ')[0]
        return None

    def _saypick(self, msg):
        if msg in self.saynotice:
            return 'notice'
        else:
            return 'msg'

    def grant(self, grant_block):
        user, achievement = grant_block.split(None, 1)
        if not self._achname(achievement):
            return (self._saypick('grant_nofound'), 'Achievement not found!') #grant_notfound
        if achievement.lower() in self.earned(user)[1].lower():
            return (self._saypick('grant_earned'), 'Achievement already earned') #grant_earned
        with open(self.userfile, 'a') as record:
            record.write('%s -> %s\n' % (user, self._achname(achievement)))
            record.flush()
        return (self._saypick('grant_success'), 'Achievement unlocked! %s has earned the achievement %s!' % (user, achievement)) #grant_success

    def earned(self, user):
        earned = ', '.join([ line.strip().split(None, 2)[2] for line in open(self.userfile, 'r') if line.split()[0] == user ])
        return (self._saypick('earned'), 'User %s has earned %s' % (user, earned)) #earned

    def add(self, achieve_block):
        parts = achieve_block.split(' : ')
        if len(parts) < 2:
            return (self._saypick('add_nodesc'), 'Achievement not added: I need a name and a description') #add_nodesc
        if self._achname(parts[0]):
            return (self._saypick('add_exists'), 'Achievement not added: Achievement with that name already exists!') #add_exists
        with open(self.achievefile, 'a') as achievements:
            achievements.write(achieve_block + '\n')
            achievements.flush()
        return (self._saypick('add_success'), 'Added new achievement: %s' % (parts[0])) #add_success

    def listachieve(self):
        achievements = ', '.join([ line.split(' : ', 1)[0] for line in open(self.achievefile, 'r') ])
        return (self._saypick('listachieve'), 'List of achievements: %s' % (achievements)) #listachieve

    def info(self, achievement):
        for line in open(self.achievefile, 'r'):
            if line.partition(' : ')[0].lower() == achievement.lower():
                parts = line.strip().split(' : ')
                return (self._saypick('info_success'), '%s: %s' % (parts[0], parts[1])) #info_success
        return (self._saypick('info_nofound'), 'Achievement not found!') #info_notfound

    def help(self):
        script = ['I am Achievebot, made to track IRC achievements',
                'Commands:',
                'grant <user> <achievement> -> Grant achievement to user',
                'earned <user> -> Display all of the achievements the user has earned',
                'listachieve -> List all available achievements',
                'add <name> : <description> -> Add a new achievement to the system',
                'info <achievement> -> Show the full block of info on the specified achievement',
                'help -> Display this help',
                'join <channel> -> Join the specified channel',
                'leave <channel> -> Leave the specified channel',
                'quit -> Quit IRC',
                'More information and source code can be found at https://github.com/dharwood/Achievebot']
        return (self._saypick('help'), '\n'.join(script)) #help

class AchieveBot(irc.IRCClient):
    """
    An IRC bot to grant and keep track of achievements users earn.
    """

    nickname = "achievebot"
    lineRate = 0.2
    nickpass = None
    channels = ''

    def __init__(self, ircopts):
        for setting in ircopts:
            getattr(self, setting[0], setting[1])

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.achieve = AchievementHandler(self.factory.appopts)
        for chan in self.channels.split():
            self.join(*chan.split())

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
            if user in self.achieve.admins:
                self.quit(message="I have been told to leave")
            else:
                self.msg(channel, "%s: No. And you can't make me." % (user))
        elif msg.startswith("join"):
            if user in self.achieve.admins:
                parts = msg.split()
                if len(parts) > 2:
                    self.join(parts[1], key=parts[2])
                else:
                    self.join(parts[1])
            else:
                self.msg(channel, 'No.')
        elif msg.startswith("leave"):
            if user in self.achieve.admins:
                self.leave(msg.split()[1], reason="I've been told to part")
            else:
                self.msg(channel, 'Not gonna happen')
        elif msg.startswith('reload'):
            if user in self.achieve.admins:
                self.reload()
            else:
                self.msg(channel, 'I change myself only for admins')
        else:
            vol, output = self.achieve.command(user, channel, msg)
            getattr(self, vol)(channel, output)

    def reload(self):
        self.factory.reload()
        for setting in self.factory.ircopts:
            if setting[0] == 'nickname' and setting[1] != self.nickname:
                self.setNick(setting[1])
            setattr(self, setting[0], setting[1])
        self.achieve.reload(self.factory.appopts)

class AchieveBotFactory(protocol.ClientFactory):
    """
    A factory for AchieveBots.
    """

    def __init__(self, config, ircopts, appopts):
        self.config = config
        self.ircopts = ircopts
        self.appopts = appopts

    def buildProtocol(self, addr):
        p = AchieveBot(self.ircopts)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        reactor.stop()
        #reconnect if connection lost
        #connector.connect()


    def clientConnectionFailed(self, connector, reason):
        reactor.stop()

    def reload(self):
        conf = RawConfigParser()
        conf.read(self.config)
        self.ircopts = conf.items('IRC Options')
        self.appopts = conf.items('Achievement Options')


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

    f = AchieveBotFactory(args.config, conf.items('IRC Options'), conf.items('Achievement Options'))
    if usessl:
        reactor.connectSSL(serv, port, f, ssl.CertificateOptions())
    else:
        reactor.connectTCP(serv, port, f)
    reactor.run()

