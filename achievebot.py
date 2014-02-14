#Twisted imports
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc

#system imports
import time, sys
from ConfigParser import RawConfigParser

class AchievementHandler:
    """
    The class that handles the actual achievements, who gets them, who doesn't, etc.
    """

    def __init__(self, config):
        #TODO: read config file, make settings changes as needed
        pass

    def grant(self, user, achievement):
        #TODO: grant the actual achievement to the user, add the user if they're not in the Users table already
        pass

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
        self.achieve = AchievementHandler(open(self.factory.config, 'r'))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.achieve.close()

class AchieveBotFactory(protocol.ClientFactory):
    """
    A factory for AchieveBots.
    """

    protocol = AchieveBot

    def __init__(self, config='abot.conf'):
        self.config = config

    def clientConnectionLost(self, connector, reason):
        #reconnect if connection lost
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()

if __name__ == '__main__':
    #TODO: get stuff working here
    f = AchieveBotFactory()
    reactor.connectSSL('irc.cat.pdx.edu', 6697, f, ssl.CertificateOptions())
    reactor.run()

