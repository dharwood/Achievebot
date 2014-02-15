#Twisted imports
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc

#system imports
import time, sys, argparse, csv
from ConfigParser import RawConfigParser

class AchievementHandler:
    """
    The class that handles the actual achievements, who gets them, who doesn't, etc.
    """

    achievefile = 'achievements'
    userfile = 'users'

    def __init__(self, config):
        #TODO: read config file, make settings changes as needed
        pass

    def command(self, user, channel, msg):
        #TODO: do application-specific command
        parse = msg.split(None, 2)
        if parse[0] == 'grant':
            return self.grant(parse[1], parse[2])
        else:
            return "Command %s not found" % (parse[0])
        pass

    def grant(self, user, achievement):
        for line in open(self.achievefile, 'r'):
            if line.partition(' : ')[0] == achievement:
                exists = True
                break
        if not exists:
            return 'Achievement not found!'
        record = open(self.userfile, 'a')
        record.write('%s -> %s\n' % (user, achievement))
        record.flush()
        return 'Achievement unlocked! %s has earned the achievement %s!' % (user, achievement)

    def ungrant(self, user, achievement):
        #TODO: remove the achievement from the user
        pass

    def add_achievement(self, name, description=None, requirement=None):
        #TODO: add new descriptions to the database
        pass

    def close(self):
        #TODO: close the connection to the database, finish things out
        pass

class AchieveBot(irc.IRCClient):
    """
    An IRC bot to grant and keep track of achievements users earn.
    """

    nickname = "achievebot"

    #needed methods: connectionMade, connectionLost

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.achieve = AchievementHandler(self.factory.appopts)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.achieve.close()

    def privmsg(self, user, channel, msg):
        if channel == self.nickname:
            self.command(user, user, msg)
        elif msg.startswith(self.nickname):
            self.command(user, channel, msg.split(None, 1)[1])

    def command(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if msg.startswith("quit"):
            self.quit(message="I have been told to leave")
        elif msg.startswith("join"):
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

