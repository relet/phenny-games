#!/usr/bin/env python
"""a taboo extension for phenny
(c)opyleft 2008-2009 Thomas Hirsch
Licence: GPL"""

import bz2, random, time, yaml, re
from operator import itemgetter
from math import floor

dico = {}

commonwords = []
#commonwords = ['SUCH', 'THAT', 'THAN', 'WHICH', 'FROM', 'WITH', 'OTHER', 'SOME', 'THEIR', 'WHOSE', 'PASS', 'WHERE', 'BEING', 'USED', 'BEEN']

words = bz2.BZ2File("wordlist/wiktionary.txt.bz2","r")
index = None
for line in words:
  if index:
    if not ':' in index:
      dico[index]=re.sub('[^A-Z ]',' ',line.strip().upper())
    index = None
  else:
    index = re.sub('[^A-Z: ]', '', line.strip().upper())

def uniq(seq):
  "eliminates duplicates from a list"
  if len(seq)<2: 
    return seq
  rest = uniq(seq[1:])
  if seq[0] in rest:
    return rest
  else:
    return [seq[0]]+rest

def setup(self):
  try:
    yamldata = open("taboo.yaml",'r')
    self.taboo = yaml.load(yamldata.read())
  except:
    self.taboo={}
    self.taboo['run']=False   
    self.taboo['scores']={}

def initgame(phenny, input):
  phenny.taboo['clue']=False  
  phenny.taboo['taboo']=False 
  phenny.taboo['run']=True
  phenny.taboo['lines']=0
  phenny.taboo['time']=time.time()
  phenny.taboo['round']={}

playtime = 301

def taboo(phenny, input):
  if phenny.taboo['run']:
    return
  initgame(phenny, input)
  while True:
    if not phenny.taboo['clue']:
      while True:
        clue = random.choice(dico.keys())
        boos = uniq(sorted([x for x in dico[clue].split() if len(x)>3]))
        for com in commonwords:
          if com in boos:
            boos.remove(com)
        phenny.taboo['clue']=clue
        phenny.taboo['boos']=boos
	if len(boos)>2: 
          break
      phenny.taboo['player']=input.nick
      phenny.bot.msg(input.nick,"describe "+clue+" without using any of "+reduce(lambda x,y:x+", "+y, boos)) #private message to originator
      tdiff = playtime - (time.time()-phenny.taboo['time']) 
      tmin  = int(floor(tdiff/60))
      tstr = str(tmin) + " minutes " + str(int(floor(tdiff-tmin*60))) + " seconds"
      phenny.say("Taboo: Off we go! "+tstr+" and counting..")
    else:
      time.sleep(1) 
    if time.time() > phenny.taboo['time'] + playtime:
      phenny.say("Time out.")
      break
    if phenny.taboo['taboo']==True: #A taboo word was said
      break
  score = phenny.taboo['round']
  if len(score)>0:
    msg = 'Taboo results: '
    for player in score:
      scr = score[player]
      phenny.taboo['scores'][player]=phenny.taboo['scores'].get(player,0)+scr
      msg += player+": "+str(scr)+"; "
    phenny.taboo['run'] = False 
    yamldump = open("taboo.yaml",'w') #save teh permanent scores
    yamldump.write(yaml.dump(phenny.taboo))
    yamldump.close()
    phenny.say(msg)
  phenny.taboo['run'] = False

taboo.commands=["taboo"]
taboo.thread=True
taboo.priority='low'

def tabooanswer(phenny, input):
  if phenny.taboo['run']==False:
    return
  if phenny.taboo['clue']==False:
    return
  answer = re.sub('[^A-Z]','',input.strip().upper())
  nospaceclue = re.sub(' ','',phenny.taboo['clue'])
  if input.nick == phenny.taboo['player']:
    phenny.taboo['lines']=phenny.taboo.get('lines',0)+1 #count the clues needed
    for boo in phenny.taboo['boos']:
      if boo in answer:
        phenny.say("TABOO!")
        phenny.taboo['taboo']=True
        return #to avoid double mentions
    if nospaceclue in answer:
      phenny.say("DOUBLE BOO!")
      phenny.taboo['taboo']=True
      phenny.taboo['round'][input.nick]=0
  else:
    if answer == nospaceclue:
      pscore = phenny.taboo['round'].get(phenny.taboo['player'],0)+1
      ascore = phenny.taboo['round'].get(input.nick,0)+1
      phenny.say(input.nick+": "+phenny.taboo['clue']+" is correct! You score "+str(ascore)+", "+phenny.taboo['player']+" scores "+str(pscore)+".")
      phenny.taboo['round'][phenny.taboo['player']]=pscore
      phenny.taboo['round'][input.nick]=ascore
      phenny.taboo['clue']=False #ok for next word

tabooanswer.rule=".*?"
tabooanswer.thread=True
tabooanswer.priority='high'

def taboopass(phenny, input):
  if phenny.taboo['run']:
    if input.nick == phenny.taboo['player']:
      phenny.taboo['clue']=False
      phenny.say("Passed.")
taboopass.commands=["pass"]
taboopass.priority='low'

def thof(phenny,input):
  total = phenny.taboo['scores']
  msg = 'Total scores: '
  ordered = sorted(total.items(), key=itemgetter(1), reverse = True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
thof.commands=["thof","ttop","taboohof","tabootop"]
thof.priority='low'  

