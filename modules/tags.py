#!/usr/bin/env python
# a phenny tags/attribute/doodle game module

import bz2, random, time, re

MINPLAYERS=1
WINNINGSCORE = 10 #may be reset

STATUS_NONE        = None
STATUS_WAITTOPIC   = 1
STATUS_TOPICSET    = 2
STATUS_WAITCARDS   = 3
STATUS_CARDSPLAYED = 4
STATUS_WAIT3SEC    = 5
STATUS_TAGGING     = 6
STATUS_RESOLVE     = 7

adj = []
data = bz2.BZ2File("wordlist/enadj.txt.bz2", "r")
for line in data:
  adj.append(line.strip().lower())

def stamp(phenny):
  phenny.doodle['lastaction']=time.time()
def unstamp(phenny):
  phenny.doodle['lastaction']=None

def shufflePlayers(phenny):
  players = phenny.doodle['players']
  if len(players)<2:
    return
  players = players[1:]+[players[0]]
  phenny.doodle['players']=players

def printScores(phenny):
  str = "Totals: "
  for player in phenny.doodle['players']:
    str += "%s: %i; " % (player, phenny.doodle['scores'][player])
  phenny.say(str)

def nextround(self):
  printScores(self)
  self.doodle['table']=[]
  for player in self.doodle['players']:
    if len(self.doodle['hands'][player])<6:
      self.doodle['hands'][player].append(random.choice(adj))
      sendCards(self, player)
    goodOrBad(self, player)
  shufflePlayers(self)
  self.doodle['status']=STATUS_NONE
  unstamp(self)

def resetgame(self):
  self.doodle['hands']={}
  self.doodle['good']={}
  self.doodle['played']={}
  self.doodle['status']=None
  self.doodle['lastaction']=None
  self.doodle['table']=[]
  self.doodle['players']=[]
  self.doodle['tags']=[]
  self.doodle['scores']={}

def setup(self):
  self.doodle={}
  self.doodle['run']=False
  resetgame(self)

def djoin(phenny, input):
  if phenny.doodle['run']:
    return
  nick = input.nick
  players = phenny.doodle['players']
  if not nick in players:
    players.append(nick)
    phenny.say(nick+" joined the game.")
djoin.commands = ["tags","tjoin"]
djoin.thread   = False

#TEST THIS!
def dquit(phenny, input):
  nick = input.nick
  players = phenny.doodle['players']
  if nick in players:
    players.remove(nick)
    phenny.say(nick+" left the game.")
dquit.commands = ["tquit","tleave"]
dquit.thread   = False

def gethand():
  hand = []
  for i in range(6):
    hand.append(random.choice(adj))
  return hand

def cardstr(cards):
  str = ""
  for card in cards:
    str += "[%s] " % card
  return str

def sendCards(phenny, player):
  cards = phenny.doodle['hands'][player]
  phenny.bot.msg(player, cardstr(cards))

def goodOrBad(phenny, player):
  good = random.randint(0,1) and True or False
  phenny.doodle['good'][player]= good
  phenny.bot.msg(player, "Please play a card that %s the topic." % (good and "matches" or "DOES NOT match"))

def drun(phenny, input):
  if phenny.doodle['run']:
    return
  try: 
    WINNINGSCORE = min(100,max(5,int(input[6:])))
  except:
    WINNINGSCORE = 10
  players = phenny.doodle['players']
  if len(players)>=MINPLAYERS:
    phenny.say("Ok, let's play a game of tags. %i points win the game" % (WINNINGSCORE))
    for player in players:
      phenny.doodle['hands'][player]=gethand()
      phenny.doodle['scores'][player]=0
      sendCards(phenny, player)
      goodOrBad(phenny, player)
    phenny.say("The cards have been dealt.")
    phenny.doodle['run']=True
    dthread(phenny)
  else:
    phenny.say("There's no one here to tag with.")
drun.commands = ["trun"]
drun.thread=True

def cardsWithTags(phenny):
  str = ""
  for card in phenny.doodle['table']:
    str += "[%s:%s] " % (card[0],card[2])
  return str

def resolveDoodle(phenny):
  for card in phenny.doodle['table']:
    carder = card[1]
    good = phenny.doodle['good'][carder]
    suggestion = card[0]
    tagger = len(card)>3 and card[3]
    score1 = ((good and tagger) or (not good and not tagger)) and 1 or -1
    score2 = good and 1 or -1
    str = "%s found it %s%s" % (carder, suggestion, good and ". " or " - NOT! ")
    if tagger:
      str += "%s is %s. (both scoring %s)" % (tagger, good and "right" or "wrong", score1)
      phenny.doodle['scores'][tagger]+=score2
    else:
      str += "And nobody agreed. (scoring %s)" % (score1)
    phenny.doodle['scores'][carder]+=score1
    phenny.say(str)
  for player in phenny.doodle['players']:
    if phenny.doodle['scores'].get(player,0)>=WINNINGSCORE:
      phenny.say("%s WINS the game!" % (player))
      phenny.doodle['run']=False

def dthread(phenny):
  while len(phenny.doodle['players'])>=MINPLAYERS and phenny.doodle['run']:
    status = phenny.doodle['status']
    last = phenny.doodle['lastaction']
    if not last:
      stamp(phenny)
      if status == STATUS_NONE: #selecting player to begin
        phenny.say("%s, please give us a topic to .discuss." % phenny.doodle['players'][0])
        phenny.doodle['status'] = STATUS_WAITTOPIC
      elif status == STATUS_TOPICSET: #waiting for cards to be dealt.
        phenny.doodle['tags']=[]
        nobodyPlayed(phenny)
        phenny.say("You may play your cards now!")
        phenny.doodle['status'] = STATUS_WAITCARDS
      elif status == STATUS_CARDSPLAYED: #getting ready to rumble.
        phenny.say("Thank you all. Ready?")
        phenny.doodle['status'] = STATUS_WAIT3SEC
      elif status == STATUS_TAGGING:     #rumble!
        nobodyPlayed(phenny)
        phenny.say("Go! Enter the code to the right of a card to .tag it, or .none")
        phenny.say(cardsWithTags(phenny))
      elif status == STATUS_RESOLVE:     #stop rumbling!
        resolveDoodle(phenny)
        nextround(phenny)
        time.sleep(2)
        continue
    else:
      if status == STATUS_WAITTOPIC:
        if time.time() > last + 60:
          phenny.say("Time out.") 
          shufflePlayers(phenny)
          phenny.doodle['status'] = STATUS_NONE
          unstamp(phenny)
      elif status == STATUS_WAITTOPIC:
        if time.time() > last + 120:
          phenny.say("Time out.") 
          phenny.doodle['status'] = STATUS_CARDSPLAYED
          unstamp(phenny)
      elif status == STATUS_WAIT3SEC:
        if time.time() > last + 3:
          phenny.doodle['status'] = STATUS_TAGGING
          unstamp(phenny)
      if status == STATUS_TAGGING:
        if time.time() > last + 60:
          phenny.say("Time out.")
          phenny.doodle['status'] = STATUS_RESOLVE
          unstamp(phenny) 
    time.sleep(1)
  if phenny.doodle['run']:
    phenny.say("Stopping game due to lack of players.")
  phenny.doodle['run']=False
  resetgame(phenny)
  unstamp(phenny)

def dtag(phenny, input):
  if not phenny.doodle['run']:
    return
  if not phenny.doodle['status']==STATUS_TAGGING:
    return
  if not input.nick in phenny.doodle['players']:
    return
  if input.nick in phenny.doodle['played']:
    return
  tag = input[5:]
  match = None
  matchi = None
  for i in range(len(phenny.doodle['table'])):
    card = phenny.doodle['table'][i]
    if card[2]==tag:
      match = card
      matchi = i
  if not match:
    phenny.say("Mistagged, %s?" % input.nick)
    return
  if match[1]==input.nick:
    phenny.say("Tagging your own card, %s?" % input.nick)
    return
  elif len(match)>3:
    phenny.say("Too late, %s!" % input.nick)
    return
  match.append(input.nick)
  phenny.doodle['table'][matchi]=match
  phenny.doodle['played'][input.nick]=True
  checkAllPlayed(phenny,STATUS_RESOLVE)
dtag.commands = ["tag"]
djoin.thread  = False

def dskip(phenny, input):
  if not phenny.doodle['run']:
    return
  if not phenny.doodle['status']==STATUS_TAGGING:
    return
  if not input.nick in phenny.doodle['players']:
    return
  if input.nick in phenny.doodle['played']:
    return
  phenny.doodle['played'][input.nick]=True
  checkAllPlayed(phenny,STATUS_RESOLVE)
dskip.commands=["skip","none"]

def dtopic(phenny, input):
  if not phenny.doodle['run']:
    phenny.say("Tell us more about %s!" % input)
    return
  if not phenny.doodle['status']==STATUS_WAITTOPIC:
    phenny.say("It's not that time of year, %s." % input.nick)
    return   
  if input.nick == phenny.doodle['players'][0]:
    unstamp(phenny)
    phenny.doodle['topic']=input
    phenny.doodle['status']=STATUS_TOPICSET
  else:
    phenny.say("Bananas!")
    return
dtopic.commands=["topic", "discuss"]

def randomTag(phenny):
  tag = chr(random.randint(97,122))+chr(random.randint(97,122))+chr(random.randint(97,122))
  if tag in phenny.doodle['tags']:
    return randomTag(phenny)
  return tag

def nobodyPlayed(phenny):
  phenny.doodle['played']={}

def checkAllPlayed(phenny, nextstatus):
  players = phenny.doodle['players']
  for player in players:
    if not player in phenny.doodle['played']:
      return False
  nobodyPlayed(phenny) 
  phenny.doodle['status']=nextstatus
  unstamp(phenny)

def dthats(phenny, input):
  if not phenny.doodle['run']:
    phenny.say("It sure is, %s." % input.nick)
    return
  if not phenny.doodle['status']==STATUS_WAITCARDS:
    phenny.say("It's not that time of year, %s." % input.nick)
    return   
  if input.nick in phenny.doodle['players']:
    suggestion = input[input.find(' ')+1:]
    if suggestion in phenny.doodle['hands'][input.nick]:
      phenny.doodle['played'][input.nick]=True
      phenny.doodle['hands'][input.nick].remove(suggestion)
      phenny.doodle['table'].append([suggestion, input.nick, randomTag(phenny)])
      checkAllPlayed(phenny,STATUS_CARDSPLAYED)
    else:
      phenny.say("That's not on your hand, %s." % input.nick)
  else:
    phenny.say("Onions!")
    return    
dthats.commands=["that's"]

def drefresh(phenny, input):
  if not phenny.doodle['run']:
    return
  nick = input.nick
  if nick in phenny.doodle['players']:
    hand = phenny.doodle['hands'][nick]
    phenny.bot.msg(nick, ""+cardstr(hand))
drefresh.commands=["cards"]

