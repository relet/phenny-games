#!/usr/bin/env python
"""
trivia.py - Phenny Wikipedia Trivia Module
Copyleft 2008, Thomas Hirsch, http://relet.net
Licensed under (among possibly others) the GPLv2
"""

from urllib2 import urlopen, Request
from operator import itemgetter
from time import time, sleep
import re, traceback, random
import yaml, bz2

useragent = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4"
url = "http://en.wikipedia.org/wiki/Special:Random"
headers = {'User-Agent:': useragent }
config = "/home/relet.net/.phenny/trivia.yaml"

re_trivial = "'''+(.*?)'''+[^\.\n]*? (is|was|are|were|will be|can be|consists of) (.*?)\."
cp_trivial = re.compile(re_trivial)

re_paragraph = "'''+(.*?)'''+[^\.\n]*? (is|was|are|were|will be|can be|consists of) (.*?)\n"
cp_paragraph = re.compile(re_paragraph)

whitelist = bz2.BZ2File("wordlist/top100k.bz2", "r")
pages = []
for line in whitelist:
  pages.append(line.split()[1])
    
def setup(self):
  try:
    yamldata = open(config,'r')
    self.trivia = yaml.load(yamldata.read())
  except:
    self.trivia = {}
    self.trivia['scores'] = {}
    self.trivia['mode'] = 'paragraph'
    self.trivia['source'] = 'random'
  self.trivia['count'] = 0
  self.trivia['round'] = {}
  self.trivia['lastaction']=time()
  reset_trivia(self)

def reset_trivia(phenny):
  phenny.trivia['clue'] = None
  phenny.trivia['solution'] = None
  phenny.trivia['hidden'] = None
  phenny.trivia['level'] = 0

def trivia(phenny, input): 
  if phenny.trivia['clue']:
    numq = phenny.trivia['startcount']-phenny.trivia['count']
    phenny.say(str(numq)+": "+phenny.trivia['clue'])
    return

  put = input[8:]
  try:
    number = int(put)
    if number<1: number = 10
    if number>1000: number = 1000
  except:
    number = 10
  phenny.trivia['count']=number
  phenny.trivia['startcount']=number
  phenny.trivia['round'] = {}
  new_trivia(phenny)
  
def stop(phenny, input):
  phenny.trivia['count'] = 0
  reset_trivia(phenny)
  phenny.say("Trivia is over - for now.")
  scores(phenny, input)
stop.commands=['strivia','stop']
stop.priority='high'
stop.thread=False

def new_trivia(phenny):
  count = phenny.trivia['count']
  if count < 1: 
    stop(phenny, ".stop")
    return 
  
  #wait for a few seconds.
  sleep(3)

  if phenny.trivia['source']=='random':
    #fetch Special:Random
    request = Request(url, None, headers)
    data = urlopen(request)

    #see where it has redirected us
    pageurl = data.geturl()
    pagetitle = pageurl[29:]
  else: 
    #choose one page from the wordlist
    pagetitle = random.choice(pages)
  phenny.trivia['lasttitle'] = pagetitle

  #refetch that page as raw wiki code
  try: 
    rawurl = "http://en.wikipedia.org/w/index.php?title="+pagetitle+"&action=raw"
    request2 = Request(rawurl, None, headers)
    data2 = urlopen(request2)
    content = data2.read()
  except:
    phenny.say("URL not found: "+rawurl)
    new_trivia(phenny)
    return

  #strip content from all possible wiki tags
  rawdata = content
  abbreviations = ['appr','ca']
  for i in range(0,100): #a while true with an escape path
    oldrawdata = rawdata
    #strip dots, at least in wikilinks
    rawdata = re.sub('(?P<one>\[\[[^\]]*)\.+(?P<two>[^\]]*\]\])','\g<one>\g<two>', rawdata)
    #FIXME: currently, the dot in f.e. an abbr. is not distinguishable from a full stop.
    #strip <ref..>..</ref> tags.
    rawdata = re.sub('<ref.*?>.*?</ref>','', rawdata)
    rawdata = re.sub('<ref.*?/>','', rawdata)
    rawdata = re.sub('\{\{.*?\}\}','', rawdata) #rm all templates. all.
    if oldrawdata == rawdata: 
      break
  for abbr in abbreviations:
    rawdata = re.sub(" "+abbr+"\.", " "+abbr, rawdata)
  rawdata = re.sub('\[\[([^\]]*?\|)?(?P<text>.*?)\]\]','\g<text>', rawdata)
  rawdata = re.sub('&nbsp;','', rawdata) #str replace would do fine

  if phenny.trivia['mode'] == 'paragraph':
    findings = re.findall(cp_paragraph, rawdata)
  else:
    findings = re.findall(cp_trivial, rawdata)

  if len(findings)>0:
    count = count - 1  
    phenny.trivia['count'] = count
    solution = findings[0][0]
    clue = findings[0][2]
    clue = clue.replace('\'','')
    clue = clue.replace('*','')
    clue = clue[0:400] #character limit. extend by ...
    if len(clue)==400:
      if clue.rfind(" ")>-1:
        clue = clue[0:clue.rfind(" ")]+"..."
    #create the "hidden" version of the solution
    hidden = re.sub('[A-Za-z0-9]','_', solution)

    #replace any words of the solution with ~~~
    words = solution.split()
    for word in words:
      if len(word)>3:
        clue = re.sub("(?i)"+re.escape(word), '~~~', clue) 

    phenny.trivia['clue'] = clue
    phenny.trivia['solution'] = solution
    phenny.trivia['lastclue'] = clue
    phenny.trivia['lastsolution'] = solution
    phenny.trivia['hidden'] = hidden
    numq = phenny.trivia['startcount']-phenny.trivia['count']
    phenny.say(str(numq)+": "+clue)
    phenny.trivia['lastaction']=time()
  elif content.find('may refer to')>-1:
    phenny.say(pagetitle+" seems to be a disambiguation page, sorry.")
    new_trivia(phenny)
    return
  elif content.find('ist of')>-1:
    phenny.say(pagetitle+" seems to be one of those annoying lists of everything and nothing, sorry.")
    new_trivia(phenny)
    return
  else: #a default fallback still has to be implemented
    logs = open('fails.log','aw')
    logs.write(pagetitle+"\n")
    logs.write(rawdata+"\n")
    logs.write("----\n")
    logs.close()
    phenny.say("I was not yet able to parse the page "+pagetitle+", sorry.")
    new_trivia(phenny)
    return

trivia.commands = ['trivia']
trivia.priority = 'high'
trivia.thread=False

def check_timer(phenny):
  if phenny.trivia['solution']:
    last = phenny.trivia['lastaction']
    if time()>last + 5.0:
      hint(phenny, "...")

def build_hint(hidden, solution, level, phenny, input):
  nruter = ""
  count = 0
  spare = 0
  for i in range(0,len(solution)):
    if solution[i]==' ':
      count = 0	
    if count < level:
      nruter += solution[i]
    else: 
      nruter += hidden[i]
      spare += 1
    count+=1
  if spare<3:
    solve(phenny, input)
    return ""
  else: 
    return nruter + " ("+str(max(1, 10 - 2 * level))+" points)"

def hint(phenny, input): 
  if phenny.trivia['hidden']:
    phenny.trivia['level'] += 1
    level = phenny.trivia['level']
    hidden = phenny.trivia['hidden']
    solution = phenny.trivia['solution']
    phenny.say(build_hint(hidden, solution, level, phenny, input))
    phenny.trivia['lastaction']=time()
  else:
    phenny.say("Try .trivia first.")

#hint.commands = ['hint','wtf','what']
#hint.priority = 'low'
#hint.thread=False

def mode(phenny, input): 
  if input == ".mode":
    phenny.say("Currently in "+phenny.trivia['mode']+" mode.")
  elif input == ".mode paragraph":
    phenny.trivia['mode'] = 'paragraph'
    phenny.say("Ok. We're now in paragraph mode.")
  else: 
    phenny.trivia['mode'] = 'line'
    phenny.say("Ok. We're now in line mode.")
mode.commands = ['mode']
mode.priority = 'low'
mode.thread=False

def source(phenny, input): 
  if input == ".source":
    phenny.say("Currently using "+phenny.trivia['source']+" source.")
  elif input == ".source random":
    phenny.trivia['source'] = 'random'
    phenny.say("Ok. Using Special:Random as trivia input.")
  else: 
    phenny.trivia['source'] = 'list'
    phenny.say("Ok. We're now using the wordlist.")
source.commands = ['source']
source.priority = 'low'
source.thread=False

def solve(phenny, input): 
  if phenny.trivia['solution']:
    phenny.say("A: "+phenny.trivia['solution'])
    reset_trivia(phenny)
    new_trivia(phenny) #check if there's some more
  else:
    phenny.say("Try .trivia first.")
solve.commands = ['solve']
solve.priority = 'low'
solve.thread=False

def scores(phenny, input):
  scores = phenny.trivia['round']
  ordered = sorted(scores.items(), key=itemgetter(1), reverse=True)
  msg = "This round: "
  for pair in ordered:
    msg += pair[0]+": "+str(pair[1])+"; "
  phenny.say(msg)  
scores.commands = ['scores', 'score']
scores.priority = 'low'
scores.thread=False

def hof(phenny, input):
  scores = phenny.trivia['scores']
  ordered = sorted(scores.items(), key=itemgetter(1), reverse=True)
  msg = "Total trivia scores: "
  for pair in ordered[0:10]:
    msg += pair[0]+": "+str(pair[1])+"; "
  phenny.say(msg)  
hof.commands = ['hof', 'top']
hof.priority = 'low'
hof.thread=False

def canonical(string):
  canon = re.sub('[^a-zA-Z0-9]','',string).lower()
  canon = re.sub('s\b','',canon)
  return canon	
  
def answer(phenny, input):
  if phenny.trivia['solution']:
    if canonical(phenny.trivia['solution'])==canonical(input):
      scores = phenny.trivia['scores']
      thisround = phenny.trivia['round']
      nick = input.nick
      thisturn = max(1, 10 - 2 * (phenny.trivia['level']))
      if nick in scores:
        scores[nick] += thisturn
      else:
        scores[nick] = thisturn
      if nick in thisround:
        thisround[nick] += thisturn
      else:
        thisround[nick] = thisturn
      phenny.trivia['scores']=scores
      yamldump = open(config,'w') #save teh permanent scores
      yamldump.write(yaml.dump(phenny.trivia))
      yamldump.close()
      phenny.trivia['round']=thisround
      phenny.say("Yay! "+nick+" is right and gains "+str(thisturn)+" points! This game: "+str(thisround[nick])+". Total: "+str(scores[nick]))
      reset_trivia(phenny)
      new_trivia(phenny) #check if there's some more
    else:
      check_timer(phenny)

answer.rule=".*" 
answer.priority='high'
answer.thread=False

def report(phenny, input):
  logs = open('reports.log','aw')
  logs.write(input+"\n")
  logs.write(phenny.trivia['lasttitle']+"\n")
  logs.write(phenny.trivia['lastclue']+"\n")
  logs.write(phenny.trivia['lastsolution']+"\n")
  logs.write("---\n")
  logs.close()
  phenny.say("Thank you for your report. The question and your comment have been recorded.")
report.commands = ['report', 'r']
report.priority = 'low'
report.thread=False

if __name__ == '__main__': 
   print __doc__.strip()
