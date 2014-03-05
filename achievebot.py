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
        self.achievestruct = self.read_achievements()
        self.userstruct = self.read_users()

    def command(self, user, channel, msg):
        """
        The function to parse and handle the command given to Achievebot
        """
        try:
            parse = msg.strip().split(None, 1)
            return getattr(self, parse[0])(user, channel, parse[1] if len(parse) > 1 else None)
        except:
            return (self._saypick('command_fail'), 'What?') #command_fail

    def _saypick(self, msg):
        """
        Determine the how Achievebot says something
        """
        if msg in self.saynotice:
            return 'notice'
        else:
            return 'msg'

    def read_achievements(self):
        """
        Read the achievements saved to the achievements file and put them in a dict of Achievement objects
        """
        #an achievement has several fields: name, description, restricted, permissions
        out = dict()
        with open(self.achievefile, 'r') as ach:
            for line in ach:
                out[line.partition(' : ')[0].lower()] = self._ach_make(*line.split(' : '))
        return out

    def read_users(self):
        """
        Read the user info from the users file and put them in a dict of lists of achievement names
        """
        out = dict()
        with open(self.userfile, 'r') as users:
            for line in users:
                parts = line.partition(' -> ')
                out[parts[0].lower()] = parts[2].strip().split(';')
        return out

    def write_achievements(self):
        """
        Write all of the Achievement objects out to file
        """
        out = []
        for name in self.achievestruct.keys():
            out.append(' : '.join((name.name, name.description, name.restricted, name.perms)))
        with open(self.achievefile, 'w') as ach:
            ach.write('\n'.join(out))

    def write_users(self):
        """
        Write all of the user information out to file
        """
        with open(self.userfile, 'w') as users:
            users.write('\n'.join([' -> '.join((name, ';'.join(self.userstruct[name.lower()]))) for name in self.userstruct.keys()]))

    def append_achievement(self, achievement):
        """
        Append a new achievement to the achievements file
        """
        with open(self.achievefile, 'a') as ach:
            ach.write(' : '.join((achievement.name, achievement.description, achievement.restricted, achievement.perms)) + '\n')

    def _ach_make(self, name, description, restricted='False', perms=''):
        """
        Create and return a new Achievement object
        """
        class Achievement:
            pass
        ach = Achievement()
        ach.name = name.strip()
        ach.description = description.strip()
        ach.restricted = restricted.strip()
        ach.perms = perms.strip()
        return ach

    def grant(self, granter, channel, grant_block):
        """
        Grant an achievement to a user
        """
        user, achievement = grant_block.split(None, 1)
        if achievement.lower() in self.achievestruct:
            if user.lower() not in self.userstruct:
                return self._grant(user, self.achievestruct[achievement.lower()].name)
            if self.achievestruct[achievement.lower()].name in self.userstruct[user.lower()]:
                return (self._saypick('grant_earned'), 'Achievement already earned!') #grant_earned
            if self.achievestruct[achievement.lower()].restricted in ['True', 'true', 'yes', 'restricted']:
                perms = self.achievestruct[achievement.lower()].perms.split()
                if granter in self.admins or granter in perms:
                    return self._grant(user, self.achievestruct[achievement.lower()].name)
                else:
                    return (self._saypick('grant_permissions'), 'This achievement is restricted.') #grant_permissions
            else:
                return self._grant(user, self.achievestruct[achievement.lower()].name)
        else:
            return (self._saypick('grant_notfound'), 'Achievement not found!') #grant_notfound

    def _grant(self, user, achievement):
        if user not in self.userstruct.keys():
            self.userstruct[user.lower()] = []
        self.userstruct[user.lower()].append(achievement)
        self.write_users()
        return (self._saypick('grant_success'), 'Achievement unlocked! %s has earned the achievement %s!' % (user, achievement)) #grant_success

    def earned(self, asker, channel, user):
        """
        Display the achievements a user has earned
        """
        earned = ', '.join(self.userstruct[user.lower()])
        return (self._saypick('earned'), 'User %s has earned %s' % (user, earned)) #earned

    def add(self, adder, channel, achieve_block):
        """
        Add a new achievement
        """
        parts = achieve_block.split(' : ')
        if len(parts) < 2:
            return (self._saypick('add_nodesc'), 'Achievement not added: I need a name and a description') #add_nodesc
        if parts[0].lower() in self.achievestruct:
            return (self._saypick('add_exists'), 'Achievement not added: Achievement with that name already exists!') #add_exists
        ach = self._ach_make(*parts)
        if adder not in self.admins and ach.restricted in ['True', 'true', 'restricted', 'yes']:
            return (self._saypick('add_perms'), 'You must be an admin to add a restricted achievement') #adminadd_perms
        self.achievestruct[parts[0].lower()] = ach
        self.append_achievement(self.achievestruct[parts[0].lower()])
        return (self._saypick('add_success'), 'Added new achievement: %s' % (parts[0])) #add_success

    def listachieve(self, *args):
        """
        List all available achievements
        """
        achievements = ', '.join([self.achievestruct[ach].name for ach in self.achievestruct.keys()])
        return (self._saypick('listachieve'), 'List of achievements: %s' % (achievements)) #listachieve

    def info(self, asker, channel, achievement):
        """
        Display more information on one achievement
        """
        if achievement.lower() not in self.achievestruct:
            return (self._saypick('info_notfound'), 'Achievement not found!') #info_notfound
        ach = self.achievestruct[achievement.lower()]
        if asker in self.admins and ach.restricted in ['True', 'true', 'yes', 'restricted']:
            return (self._saypick('info_perms'), '%s: %s (restricted, allowed users: %s)' % (ach.name, ach.description, ach.perms)) #info_perms
        else:
            return (self._saypick('info_success'), '%s: %s' % (ach.name, ach.description)) #info_success

    def help(self, *args):
        """
        Display the help for Achievebot
        """
        script = ['I am Achievebot, made to track IRC achievements',
                'Commands:',
                'grant <user> <achievement> -> Grant achievement to user',
                'ungrant <user> <achievement> -> Remove an achievement from a user',
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

    def ungrant(self, asker, channel, ungrant_block):
        """
        Remove a granted achievement from a user
        """
        user, achievement = ungrant_block.split(None, 1)
        if achievement.lower() not in map(str.lower, self.userstruct[user.lower()]):
            return (self._saypick('ungrant_unearned'), 'User %s has not earned that achievement' % user) #ungrant_unearned
        self.userstruct[user.lower()].remove(self.achievestruct[achievement.lower()].name)
        self.write_users()
        return (self._saypick('ungrant_success'), "Achievement %s has been removed from %s" % (self.achievestruct[achievement.lower()].name, user)) #ungrant_success

    def reload(self, config):
        """
        Reload the configuration settings and reread the achievements and users files
        """
        for setting in config:
            setattr(self, setting[0], setting[1])
        self.achievestruct = self.read_achievements()
        self.userstruct = self.read_users()

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
            setattr(self, setting[0], setting[1])

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.achieve = AchievementHandler(self.factory.appopts)
        for chan in self.channels.split(','):
            if chan == '':
                continue
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
                self.msg(channel, 'Reload complete')
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

