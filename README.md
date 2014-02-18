# AchieveBot

An IRC bot to grant and display achievements that users earn in IRC.

## Running

AchieveBot is a Python script using the Twisted framework.
Before running the bot, you need to have the libraries for Twisted:

```sh
# pip2 Twisted
```

Note that since Twisted is currently written only for Python 2, so is AchieveBot. If/when Twisted is brought up to Python 3, Achievebot will be as well.

```
usage: achievebot.py [-h] [-c FILE] [-s SERVER] [-p PORT] [--ssl]

Bot for IRC achievements

optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        Config file to use. If it is missing, a default
                        configuration file will be generated at the same path.
  -s SERVER, --server SERVER
                        Server to connect to (overrides config file)
  -p PORT, --port PORT  Port to connect to (overrides config file)
  --ssl                 Connect using SSL (overrides config file)
```

## Configuration

Currently, the only options supported are the server to connect to, the port to use, and if SSL should be used. All other options for the client and the achievement application are unimplemented.

These options can be set in the configuration (by default, abot.conf), or when the bot is started. If there is no config file when the bot is started, a generic one is created under the name abot.conf and the program exits.

## Achievements and Users

Achievements are stored in the file 'achievements'. Each achievement is on one line and has the format:

```
<name> : <description>
```

The intention is that the description would be something somewhat silly followed by something in parentheses about how to earn the achievement (though this is completely optional).

Information about which user have earned which achievements is stored in the file 'users'. Each entry takes one line and is of the format:

```
<name> -> <achievement-name>
```

## Commands

* join &lt;channel&gt; &lt;key&gt;: Join a channel (This requires admin powers)
* leave &lt;channel&gt;: Leave a channel (This requires admin powers)
* quit: Quit and disconnect from IRC (This requires admin powers)
* add &lt;name&gt; : &lt;description&gt;: Add a new achievement and description to the system
* grant &lt;user&gt; &lt;achievement&gt;: Grant an achievement to a user
* earned &lt;user&gt;: Show a list of all the achievements the user has earned
* listachieve: Show a list of all available achievements
* info &lt;achievement&gt;: Show the full description of an achievement
* help: Show the available commands and source information
* reload: Reload the configuration settings from the configuration file (This only affects IRC Options and Achievement Options)

Admin powers are granted by placing the admins' nicks in the list admins in AchieveBotFactory.

## Current Status

Achievebot is still very young. Currently, it can connecs to the server, join and leave channels, answer to private messages, and grant, add, and display information on achievements. Giving Achievebot the command 'help' will display information about using the commands and about the bot itself.

Please note that **there is no access control**. This means that when the bot is running, anyone can tell it to join or leave any channel, add or grant any achievement, flood a channel with help or achievement info, or quit IRC altogether. Please make sure that this is OK before you start running the bot, and don't be surprised if ops kick the bot (or you) for being a problem.

## Future Plans

* Some kind of access control for users
* More options to control usage (e.g., change nickname without having to modify code, channels to join on startup, etc.)
* Code cleanup (it's a bit of a mess at the moment)
* Probably plenty more that I didn't think of while I was typing this (suggestions and pull requests always welcome)

## Copyright

This code is copyright (c) 2014 David Harwood under the terms of the MIT License, a copy of which is in the file LICENSE
