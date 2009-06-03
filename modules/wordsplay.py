#!/usr/bin/env python
"""
wordsplay.py - Phenny Wordsplay Module
Author: Thomas Hirsch, http://relet.net
"""

from urllib2 import urlopen, Request
from random import random, randint, choice
from operator import itemgetter
import bz2, re, time, yaml

useragent = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4"
headers = {'User-Agent:': useragent }

letters = {
  'A':0.0651,
  'B':0.0189,
  'C':0.0306,
  'D':0.0508,
  'E':0.1740,
  'F':0.0166,
  'G':0.0301,
  'H':0.0476,
  'I':0.0755,
  'J':0.0027,
  'K':0.0121,
  'L':0.0344,
  'M':0.0253,
  'N':0.0978,
  'O':0.0251,
  'P':0.0079,
  'Q':0.0002,
  'R':0.0700,
  'S':0.0758,
  'T':0.0615,
  'U':0.0435,
  'V':0.0067,
  'W':0.0189,
  'X':0.0003,
  'Y':0.0004,
  'Z':0.0113,
}

def neighbours(size):
  neighs = {}
  f = size - 1
  for y in range(0,size):
    for x in range(0,size):
      pos = x + y*size
      nn = []
      if y>0:
        if x>0:  
          nn.append(pos-size-1)
        nn.append(pos-size)
        if x<f: 
          nn.append(pos-size+1)
      if x>0:
        nn.append(pos-1)
      if x<f:
        nn.append(pos+1)
      if y<f:
        if x>0:
          nn.append(pos+size-1)
        nn.append(pos+size)
        if x<f:
          nn.append(pos+size+1)
      neighs[pos]=nn
  return neighs

nb={}
for i in range(3,8):
  nb[i]=neighbours(i) #precalculate

wordlist={} #dictionaries are so much faster to lookup in
wordbits={}
  
def addword(word, wordlist):
  if len(word)<3: 
    return 
  wordlist[word]=True
  for i in range(1,len(word)):
    wordbits[word[:i]]=True

words = bz2.BZ2File("wordlist/yawl.txt.bz2","r")
for line in words:
  addword(line.strip().upper(), wordlist)

def hasword(word, wordlist):
  return (word in wordlist)
  
def findall(table, used, pos, prefix, nbtable):
  c = table[pos]
  prefix = prefix + c
  if prefix in wordlist:
    all = [prefix]
  else:
    all = []
  if prefix in wordbits:
    cur = used[:]
    cur[pos] = True
    for n in nbtable[pos]:
      if not cur[n]:
        all.extend(findall(table, cur, n, prefix, nbtable))
  return all

def allwords(table, size):
  all = []
  s2 = size * size
  used = [False]*s2
  for i in range(0,s2):
    c = table[i]
    all.extend(findall(table, used, i, '', nb[size]))
  buckets = {}
  lmax = 0
  for word in all:
    l = len(word)
    if l>lmax:
      lmax = l
    if l in buckets:
      buckets[l].append(word)
    else:
      buckets[l]=[word]
  buckets['max']=lmax
  for lw in buckets.keys():
    if not lw == 'max':
      buckets[lw]=uniq(buckets[lw])
  return buckets
  
def uniq(seq):
  "eliminates duplicates from a list"
  if len(seq)<2: 
    return seq
  rest = uniq(seq[1:])
  if seq[0] in rest:
    return rest
  else:
    return [seq[0]]+rest

#def bestwords(table, size):
#  all = allwords(table, size)
#  best = None
#  lbest = 0
#  for l in all.keys():
#    if l>lbest:
#      lbest=l
#      best=all[l]
#  return uniq(best)
    
action = chr(1)+"ACTION "
afin   = chr(1)

def setup(self):
  try:
    yamldata = open("wordsplay.yaml",'r')
    self.wordsplay = yaml.load(yamldata.read())
  except:
    self.wordsplay={}
    self.wordsplay['run']=False
    self.wordsplay['scores']={}
    self.wordsplay['best']=None
  try:
    yamldata = open("jumble.yaml",'r')
    self.jumble = yaml.load(yamldata.read())
  except:
    self.jumble={}
    self.jumble['run']=False
    self.jumble['scores']={}
  try:
    yamldata = open("three.yaml",'r')
    self.three = yaml.load(yamldata.read())
  except:
    self.three={}
    self.three['run']=False
    self.three['scores']={}

def initround(phenny, input):
  phenny.wordsplay['round']={}
  phenny.wordsplay['used']=[]
  phenny.wordsplay['run']=True

def initjumble(phenny, input):
  phenny.jumble['run']=True

def initthree(phenny, input):
  phenny.three['run']=True

def drawtable(phenny, input):
  table = phenny.wordsplay['table']
  size  = phenny.wordsplay['size']
  best  = ('best' in phenny.wordsplay) and phenny.wordsplay['best'] #and phenny.wordsplay['best'].clone()
  for i in range(0,size*size,size):
    hint = "  "
    if 'hints' in phenny.wordsplay:
      lmax = best['max']
      lcur = lmax - i/size
      if lcur>2: 
        hint += "%i letters: %i" % (lcur, (lcur in best) and len(best[lcur]) or 0)
    phenny.say('| '+reduce(lambda x,y:x+" "+y, table[i:i+size])+' |'+hint)

def weightedChoice(dic):
  select = random()
  total = 0.0
  for letter, prob in dic.iteritems():
    total += prob
    if select < total:
      return letter
  return None

def randomchar():
  return weightedChoice(letters)

def gentable(phenny, input):
  size = phenny.wordsplay['size']
  table = reduce(lambda x,y:x+y, [randomchar() for i in range(0,size*size)])
  phenny.wordsplay['table']=table

def scramble(s):
  for i in range(0,100):
    a = randint(0,len(s)-1)
    b = randint(0,len(s)-1)
    if a != b:
      x = min(a,b)
      y = max(a,b)
      s = s[:x]+s[y]+s[x+1:y]+s[x]+s[y+1:]
  return s

def genjumble(phenny, input):
  pos = randint(0,len(wordlist)-1)
  word = wordlist.keys()[pos]
  clue = scramble(word)
  phenny.jumble['issued']=time.time()
  phenny.jumble['clue']=clue
  phenny.jumble['word']=word

def cutthree(word, num, reverse):
  consonants = [c for c in word if c not in ['A','E','I','O','U']]
  first = consonants[:num]
  if reverse:
    first = consonants[-num:]
  if len(first)==num:
    ret = ""
    for c in first:
      ret = ret+c
    return ret
  return False

def genthree(phenny, input):
  clue = False
  num = 3
  try:
    num = int(input.split(" ")[1])
    num = max(3,min(num,5))
  except:
    pass
  while not clue:
    pos = randint(0,len(wordlist)-1)
    word = wordlist.keys()[pos]
    phenny.three['solve']=word
    clue = cutthree(word,num,False)
  if randint(0,1): #one out of two clues is reversed.
    reverse = ''
    for c in clue:
      reverse = c+reverse
    clue = reverse
  phenny.three['clue']=clue

def checkRec(table, used, input, lastpos, ntable):
  #print "checkRec ",input,lastpos
  if len(input)==0:
    return True
  use = used[:]
  use[lastpos] = True
  for a in ntable[lastpos]:
    #print "Next",a
    if (table[a]==input[0]) and (not use[a]):
      if checkRec(table, use, input[1:], a, ntable):
        return True
  return False

def checkWord(phenny,input):
  #print "checking ",input
  if len(input)<3: 
    return False
  table = phenny.wordsplay['table']
  size  = phenny.wordsplay['size']
  #print "on ",table
  s2 = size*size
  ntable = nb[size]
  data = [False]*s2
  ret = False
  for p in range(0,s2):
    if table[p]==input[0]:
      if checkRec(table, data, input[1:], p, ntable):
        ret = True
  return ret

def jumble(phenny,input):
  if phenny.jumble['run']:
    phenny.say("jumble this: "+phenny.jumble['clue'])
    return
  genjumble(phenny,input)
  #print phenny.jumble['word']
  initjumble(phenny,input)
  phenny.say("jumble this: "+phenny.jumble['clue'])
jumble.commands=["jumble","scramble"]
jumble.priority="low"
jumble.thread=False

def three(phenny,input):
  if phenny.three['run']:
    phenny.say("Find a word beginning with these consonants in order: "+phenny.three['clue'])
    return
  genthree(phenny,input)
  initthree(phenny,input)
  phenny.say("Find a word beginning with these consonants in order: "+phenny.three['clue'])
three.commands=["three"]
three.priority="low"
three.thread=False

def wordsplay(phenny, input): 
  if phenny.wordsplay['run']:
    drawtable(phenny, input)
    return
  size = 4
  hints = False 
  try:
    data = input.split(" ")
    par = data[1]
    if data[1]=="hints":
      hints = True
    size = int(par)
    hints = data[2]=="hints"
  except:
    pass
  if size<3 or size>7:
    phenny.say("Only table sizes 3x3 to 7x7 are enabled right now.")
    return
  phenny.wordsplay['size']=size    
  gentable(phenny, input)  
  initround(phenny,input)
  solution = allwords(phenny.wordsplay['table'], size) 
  phenny.wordsplay['hints']=None
  if hints:
    phenny.wordsplay['hints']=True
  phenny.wordsplay['best']=solution
  drawtable(phenny, input)
  time.sleep(120)
  phenny.say("1 minute left...")
  time.sleep(50)
  phenny.say("10 seconds...")
  time.sleep(10)
  phenny.wordsplay['run']=False
  scores = phenny.wordsplay['round']
  total = phenny.wordsplay['scores']
  msg = ' '
  pbest = 0
  for nick in scores:
    total[nick] = total.get(nick,0) + scores[nick][1]
    if scores[nick][0]>pbest:
      pbest = scores[nick][0]
  ordered = sorted(scores.items(), key=itemgetter(1), reverse=True)
  for entry in ordered:
    msg += entry[0]+": "+str(entry[1][1])+" (total: "+str(total[entry[0]])+"); "
  phenny.say("Round is over."+msg)
  lbest = solution['max']
  if lbest == pbest:
    phenny.say("PERFECT!")
  best = solution[lbest]
  for word in best[:]:
    if word in phenny.wordsplay['used']:
      best.remove(word)
  while len(best)<5:
    lbest -= 1
    best.extend(solution[lbest])
    for word in best[:]:
      if word in phenny.wordsplay['used']:
        best.remove(word)
  if len(best)>0:
    etc = (len(best)>5) and "("+str(len(best))+" words with "+str(lbest)+" letters or more)" or ""
    phenny.say("Longest remaining words: "+reduce(lambda x,y:x+"; "+y, best[:5])+" "+etc)
  phenny.wordsplay['best']=None
  yamldump = open("wordsplay.yaml",'w') #save teh permanent scores
  yamldump.write(yaml.dump(phenny.wordsplay))
  yamldump.close()  

wordsplay.commands=["wordsplay", "boggle", "words"]
wordsplay.priority="low"
wordsplay.thread=True

def wscores(phenny,input):
  if not phenny.wordsplay['run']:
    return phenny.say("No game in progress.")
  scores = phenny.wordsplay['round']
  msg = 'Current scores: '
  ordered = sorted(scores.items(), key=itemgetter(1), reverse = True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1][1])+"; "
  phenny.say(msg)
wscores.commands=["wscore","wscores"]
wscores.priority='low'  

def whof(phenny,input):
  total = phenny.wordsplay['scores']
  msg = 'Total words scores: '
  ordered = sorted(total.items(), key=itemgetter(1), reverse = True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
whof.commands=["whof","wtop","wordshof","wordstop"]
whof.priority='low'  

def jhof(phenny,input):
  total = phenny.jumble['scores']
  msg = "Total jumble scores: " 
  ordered = sorted(total.items(), key=itemgetter(1), reverse=True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
jhof.commands=["jhof","jtop","jumblehof","jumbletop"]
jhof.priority='low'

def threehof(phenny,input):
  total = phenny.three['scores']
  msg = "Total 'three' scores: " 
  ordered = sorted(total.items(), key=itemgetter(1), reverse=True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
threehof.commands=["3hof","3top","threehof","threetop"]
threehof.priority='low'

def guessedBefore(phenny,input):
  guesses = phenny.wordsplay['used']
  for word in guesses:
    if input in word:
      return True
  return False

def bettered(phenny, input, nick):
  prev = phenny.wordsplay['round']
  if nick in prev:
    if len(input)<=prev[nick][0]:
      return False
  return True 

def wouldjumble(s1,s2):
  l1 = [c for c in s1]
  l2 = [c for c in s2]
  for c in l1:
    if not (c in l2):
      return False
    l2.remove(c)
  return (not l2)

def wouldthree(clue, word):
  if cutthree(word,len(clue),False)==clue:
    return True
  reverse = ""
  for c in word:
    reverse = c+reverse 
  if cutthree(reverse,len(clue),True)==clue:
    return True
  return False

def jguess(phenny, input):
  if not phenny.jumble['run']:
    return
  if phenny.jumble['issued']:
    if time.time() > phenny.jumble['issued']+7200:
      phenny.jumble['run']=False
      phenny.say("Did really no one recognize the "+phenny.jumble['word']+" in "+phenny.jumble['clue']+"? Meh.")
      return
  nick = input.nick
  input = input.upper().strip()
  word = phenny.jumble['word']
  if input == word:
    phenny.jumble['run']=False
    scores = phenny.jumble['scores']
    value = max(1,len(word)/4)
    scores[nick]=scores.get(nick,0)+value
    phenny.say(nick+" is correct and scores "+str(value)+" points for a total of "+str(scores[nick])+". "+choice(("Woo.","Yay.","Toot.","Congratulations.","Meh.")))
    yamldump = open("jumble.yaml",'w') #save teh permanent scores
    yamldump.write(yaml.dump(phenny.jumble))
    yamldump.close()
  elif (input in wordlist) and wouldjumble(input,word):
    phenny.say(nick+": Could be. But no.")

def threeguess(phenny, input):
  if not phenny.three['run']:
    return
  nick = input.nick
  input = input.upper().strip()
  if not input in wordlist:
    return
  clue = phenny.three['clue']
  if wouldthree(clue, input):
    phenny.three['run']=False
    scores = phenny.three['scores']
    value = max(0,len(clue)-2)
    scores[nick]=scores.get(nick,0)+value
    phenny.say(input+" is correct and "+nick+" scores "+str(value)+" points for a total of "+str(scores[nick])+". "+choice(("Zabang.","Oy.","Shoowap.","Clap-clap.","Houpla.")))
    yamldump = open("three.yaml",'w') #save teh permanent scores
    yamldump.write(yaml.dump(phenny.three))
    yamldump.close()

def checkBested(phenny, input, nick):
  pscore = 0
  best = phenny.wordsplay['best']
  lbest = best['max']
  prev = phenny.wordsplay['round']
  if nick in prev:
    pscore = prev[nick][0]
  if pscore == lbest:
    remains = False
    while lbest > 1 and remains==False:
      if lbest in best:
        for word in best[lbest]:
          if not word in phenny.wordsplay['used']:
            remains = True
            break
      if not remains:
        lbest -= 1
    if len(input)==lbest:
      old = phenny.wordsplay['round'].get(nick,(3,0,0)) #old word len, old score, old bonus
      bonus = old[2] + 1
      score = old[1] + 1
      phenny.wordsplay['used'].append(input)
      phenny.wordsplay['round'][nick]=(old[0],score,bonus)
      phenny.say(nick+" scores "+str(score)+" points with the bonus word "+input)

def wguess(phenny,input):
  jguess(phenny,input) #we don't have to check regexes twice.
  threeguess(phenny,input) #nor have we to check regexes thrice.
  if not phenny.wordsplay['run']:
    return
  nick = input.nick
  input = input.upper().strip()
  if not hasword(input, wordlist):
    #phenny.say("DEBUG: not in list")
    return
  if not bettered(phenny, input, nick):
    checkBested(phenny, input, nick)
    return
  if guessedBefore(phenny, input):
    #phenny.say("DEBUG: guessed before")
    return
  if not checkWord(phenny,input):
    #phenny.say("DEBUG: not on table")
    return
  old = phenny.wordsplay['round'].get(nick,(3,0,0)) #old word len, old score, old bonus
  bonus = old[2]+max(len(input)-old[0]-1,0)
  score = len(input) - 3 + bonus 
  phenny.wordsplay['used'].append(input)
  phenny.wordsplay['round'][nick]=(len(input),score,bonus)
  phenny.say(nick+" scores "+str(score)+" points with the word "+input)
wguess.rule=".*?"
wguess.priority="high"
wguess.thread=False

def threereset(phenny, input):
  if phenny.three['run']==True:
    phenny.three['run']=False
    phenny.say("As you wish. One possible solution was "+phenny.three['solve']) 
    phenny.three['solve']=""
threereset.commands=["3reset","threereset"]
threereset.priority='low'
  

def striphtml(str):
  ret = re.sub('\<.*?\>','',str)
  return ret

def check(phenny,input):
  s = input.split()
  if len(s)<2:
    return phenny.say("usage: .check word - looks up word in wordlist and on http://morewords.com")
  word = s[1]
  if not re.match("[A-Za-z]*", word):
    return phenny.say("meh. I won't check THAT.")
  inList = hasword(word.upper(), wordlist)
  phenny.say(word+" is"+(inList and " " or " -not- ")+"contained in my word list")
  url = "http://www.morewords.com/word/"+word
  request = Request(url, None, headers)
  data = urlopen(request)
  content = data.read()
  if re.search(word+" - not found",content): #checking
    inMore = False
    phenny.say(word+" was not found on morewords.com"+(inList and ", though." or ", either."))
  elif re.search('\<h2\>'+word+'\</h2\>', content): #double checking
    inMore = True 
    defs = re.findall('\<p\>\<strong\>Definitions? of '+word+'\</strong\>\<br /\>(.*?)\</p\>',content)
    if len(defs)==0:
      phenny.say(word+" is listed on morewords, but no definition was found.")
    else:
      defs=striphtml(defs[0])
      phenny.say(defs[:400])
  else: 
     phenny.say("Something funny happened while retrieving "+url)
  
check.commands=["check"]
check.priority="low"

if __name__ == '__main__': 
   print __doc__.strip()
