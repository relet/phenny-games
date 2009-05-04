#!/usr/bin/env python
# a phenny history game module

import pickle, bz2, random, time, re

MINPLAYERS=1
PENALTY=2

data = bz2.BZ2File("wordlist/cards.pickle.bz2", "r")
cards = pickle.load(data)

month=["None","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Fail"]

def setup(self):
  self.history={}
  self.history['players']=[]
  self.history['current']=None
  self.history['previous']=None
  self.history['lastaction']=None
  self.history['hands']={}
  self.history['table']=[]
  self.history['run']=False

def getcard():
  while True:
    card = random.choice(cards)
    if not re.match('[0-9]{3,4}',card[1]):
      return card

def newhand():
  hand = [getcard() for i in range(0,8)]
  return hand

def printhand(hand):
  msgs = []
  for card in range(0,len(hand)):
    if hand[card]:
      msgs.append( str(card+1)+": "+hand[card][1] )
  return msgs

def solve(hand):
  msgs = []
  for card in hand:
    sdate = ""
    date = card[0]
    if date[1]: 
      sdate += month[date[1]]  
    if date[0]: 
      sdate += " "+str(date[0])
    if sdate:
      sdate += ", "
    sdate += str(date[2])
    if date[2]<0:
      sdate = sdate[1:] + "BC"
    msgs.append(sdate+": "+card[1])
  return msgs

def hjoin(phenny, input):
  nick = input.nick
  players = phenny.history['players']
  if not nick in players:
    players.append(nick)
    hand = newhand()
    phenny.history['hands'][nick]=hand
    for line in printhand(hand):
      phenny.bot.msg(nick, line)
    phenny.say(nick+" joined the game.")
hjoin.commands = ["history","hjoin"]
hjoin.thread   = False

def hquit(phenny, input):
  nick = input.nick
  players = phenny.history['players']
  if nick in players:
    players.remove(nick)
    #todo: check current != nick
    phenny.say(nick+" left the game.")
hquit.commands = ["hquit","hleave"]
hquit.thread   = False

def hrun(phenny, input):
  if phenny.history['run']:
    return
  players = phenny.history['players']
  if len(players)>=MINPLAYERS:
    phenny.say("Ok, starting the history game.")
    table = [getcard()]
    phenny.history['table']=table
    phenny.history['run']=True
    for line in printhand(table):
      phenny.say(line)
    hthread(phenny)
  else:
    phenny.say("Not enough players.")
hrun.commands = ["hrun","hstart"]
hrun.thread=True

def hthread(phenny):
  while len(phenny.history['players'])>=MINPLAYERS and phenny.history['run']:
    last = phenny.history['lastaction']
    if not last:
      current = phenny.history['current'] or 0
      phenny.history['previous'] = current
      players = phenny.history['players']
      next = 0
      if current != None:
        next = (current + 1)%len(players)
      phenny.history['lastaction']=time.time()
      phenny.history['current']=next
      phenny.say(phenny.history['players'][next]+"'s turn.")
    elif time.time() > last + 60:
      phenny.say("Time out.") 
      #TODO: disable player upon third timeout
      phenny.history['lastaction']=None
    time.sleep(1)
  if phenny.history['run']:
    phenny.say("Stopping game due to lack of players.")
  phenny.history['run']=False

def handempty(hand):
  empty = True
  for card in hand:
    if card:
      empty = False
  return empty

def hrefresh(phenny, input):
  if not phenny.history['run']:
    return
  nick = input.nick
  if nick in phenny.history['players']:
    hand = phenny.history['hands'][nick]
    phenny.bot.msg(nick,"---")
    for line in printhand(hand):
      phenny.bot.msg(nick,line)
hrefresh.commands=["cards"]

def autocall(phenny, nick):
  phenny.say(nick+" played the last card.")
  for line in solve(phenny.history["table"]):
    phenny.say(line)
  if checkorder(phenny):
    phenny.say("The order was correct. "+nick+" WINS the game.")
    phenny.history['run']=False
    phenny.history['players']=[]
    phenny.history['hands']={}
  else:
    phenny.say("The order was incorrect. "+nick+" receives "+str(PENALTY)+" cards.")
    deal(phenny, nick, PENALTY)
    table = [getcard()]
    phenny.history['table']=table
    for line in printhand(table):
      phenny.say(line)

def hplay(phenny, input):
  nick = input.nick
  if not phenny.history['run']:
    return
  if phenny.history['players'][phenny.history['current']] != nick:
    phenny.say("Not your turn, "+nick)
    return
  hand = phenny.history['hands'][nick]
  cid, where, pid = None, None, None
  try:
    cmd = input.split(" ")
    cid = int(cmd[1])
    where = cmd[2]
    if where=="before" or where=="after":
      pid = int(cmd[3])
    card = hand[cid-1]
    if not card:
      phenny.say("You already played that card.")
      return
  except:
    phenny.say("Syntax: .card #(on hand) first|last|before #(on table)|after #(on table)")
    return
  insertpos = -1
  table=phenny.history['table']
  if where == "first":
    insertpos = 0
  elif where == "last":
    insertpos = len(table)
  elif where == "before":
    insertpos = min(len(table),max(0,pid-1))
  elif where == "after":
    insertpos = min(len(table),max(0,pid))
  if insertpos == -1:
    phenny.say("Syntax: .card #(on hand) first|last|before #(on table)|after #(on table)")
    return
  hand[cid-1]=None
  table.insert(insertpos, card)
  phenny.history['hands'][nick]=hand
  phenny.history['table']=table
  for line in printhand(table):
    phenny.say(line)
  if handempty(hand):
    autocall(phenny, nick)
  phenny.history['lastaction']=None
hplay.commands = ["card","hplay"]
hplay.thread=False

def larger(d1, d2):
  if d1[2]>d2[2]:
    return True
  elif d1[2]==d2[2]:
    if d1[1] and d2[1]:
      if d1[1]>d2[1]:
        return True
      elif d1[1]==d2[1]:
        if d1[0] and d2[0]:
          if d1[0]>d2[0]:
            return True
  return False

def checkorder(phenny):
  table = phenny.history['table']
  correct = True
  for i in range(0,len(table)-1):
    if larger(table[i][0],table[i+1][0]):
      correct = False
  return correct

def deal(phenny, nick, num):
  hands = phenny.history['hands']
  hand = hands[nick]
  for i in range (0,num):
    card = getcard()
    hand.append(card)
    phenny.bot.msg(nick, str(len(hand))+": "+card[1])

def hcall(phenny, input):
  if not phenny.history['run']:
    return
  nick = input.nick
  if phenny.history['players'][phenny.history['current']] != nick:
    phenny.say("Not your turn, "+nick)
    return
  for line in solve(phenny.history["table"]):
    phenny.say(line)
  if checkorder(phenny):
    phenny.say("The order was correct. "+nick+" receives "+str(PENALTY)+" cards.")
    deal(phenny, nick, PENALTY)
    phenny.history['lastaction']=None
    pass
  else:
    current = phenny.history['current']
    players = phenny.history['players']
    prev = (current + len(players) - 1) % len(players)
    previous = players[prev]
    phenny.say("The order was incorrect. "+previous+" receives "+str(PENALTY)+" cards. "+nick+"'s turn.")
    deal(phenny, previous, PENALTY) 
    phenny.history['lastaction']=time.time()
  table = [getcard()]
  phenny.history['table']=table
  for line in printhand(table):
    phenny.say(line)
hcall.commands = ["call"]
hcall.thread=False

