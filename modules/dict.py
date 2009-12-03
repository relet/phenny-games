#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dict.py - Phenny Dictionary Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web
from tools import deprecated
import time
import threading

wordnet_uri = 'http://wordnetweb.princeton.edu/perl/webwn?s=%s'
tfd_uri  = 'http://www.thefreedictionary.com/%s'
encarta_uri = 'http://encarta.msn.com/dictionary_/%s.html'
lexicus_uri = 'http://www.lexic.us/definition-of/%s'

r_encarta = re.compile( r'(?:ResultBody"><br /><br />(.*?)&nbsp;)|(?:<b>(.*?)</b>)' )
r_wordnet = re.compile(r'<li>(.*?)</li>')
r_lexicus = re.compile(r'Definition of.*?</h3><p>(.*?)<div')
r_tfd = re.compile(r'<tr>.*?(<b>[0-9]+\..*?)</tr>')
r_striptags = re.compile(r'<.*?>')
r_word = re.compile(r'^[A-Za-z0-9\' -]+$')

searches = {}
searches_lock = threading.Lock()
results = {}
results_lock = threading.Lock()

def searchCounter(word, diff=0):
  searches_lock.acquire()
  searches[word]=searches.get(word,0)+diff
  remaining = True
  if searches[word]<=0:
    remaining = False
    del searches[word]
  searches_lock.release()
  return remaining

def resultCounter(word, diff=0, reset=False):
  results_lock.acquire()
  results[word]=results.get(word,0)+diff
  count = results[word]
  if reset:
    del results[word]
  results_lock.release()
  return count
  
def dict(phenny, input):
   if not " " in input:
     phenny.msg(input.sender, input.nick + ": Mu.")
     return
   term = input.split(" ")[1]
   
   if not r_word.match(term): 
     msg = "Words must match the regexp %s" % r'^[A-Za-z0-9\' -]+$'
     return phenny.msg(input.sender, input.nick + ": " + msg)
   if ('--' in term) or ("''" in term) or ('  ' in term): 
     phenny.msg(input.sender, input.nick + ": Mu.")
     return

   searchCounter(term, 1)
   #SearchDict(phenny, wordnet_uri, parse_wordnet, term).start()
   #SearchDict(phenny, tfd_uri, parse_tfd, term).start()
   #SearchDict(phenny, encarta_uri, parse_encarta, term).start()
   SearchDict(phenny, lexicus_uri, parse_lexicus, term).start()
   while searchCounter(term):
     time.sleep(1)
   if resultCounter(term, reset=True)==0:
     phenny.reply("No results found for %s." % term)
dict.commands = ['dict']
dict.priority = 'low'

#THREADED DICTIONARY REQUESTS _____________________________________________
class SearchDict(threading.Thread):
  def __init__(self, phenny, uri, parser, term):
    self.uri = uri
    self.parser = parser
    self.term = term
    self.phenny = phenny
    threading.Thread.__init__(self)

  def run(self):
     bytes = web.get(self.uri % (web.urllib.quote(self.term.encode('utf-8')))) # @@ ugh!
     msg = self.parser(self.phenny, bytes, self.term)
#==========================================================================

def parse_tfd(phenny, bytes, term): 
  items = r_tfd.findall(bytes)
  msg = ""
  for item in items: 
    text = r_striptags.sub('',item)
    msg += text+"; "
  if not items: 
    #phenny.reply("I couldn't find '%s' in TheFreeDictionary." % term)
    pass
  else:
    phenny.reply(msg)
    resultCounter(term, 1)
  searchCounter(term, -1)
  return
  
def parse_wordnet(phenny, bytes, term): 
  items = r_wordnet.findall(bytes)
  msg = ""
  for item in items: 
    text = r_striptags.sub('',item)
    msg += text+"; "
  if not items: 
    #phenny.reply("I couldn't find '%s' in WordNet." % term)
    pass
  else:
    phenny.reply(msg)
    resultCounter(term, 1)
  searchCounter(term, -1)
  return

def parse_lexicus(phenny, bytes, term): 
  items = r_lexicus.findall(bytes)
  msg = ""
  for item in items: 
    text = r_striptags.sub('',item)
    msg += text+"; "
  if not items: 
    #phenny.reply("I couldn't find '%s' in Lexic.us" % term)
    pass
  else:
    phenny.reply(msg)
    resultCounter(term, 1)
  searchCounter(term, -1)
  return
  
def parse_encarta(phenny, bytes, term): 
  def trim(thing): 
     if thing.endswith('&nbsp;'): 
        thing = thing[:-6]
     return thing.strip(' :.')
  results = {}
  wordkind = None
  for kind, sense in r_encarta.findall(bytes): 
     kind, sense = trim(kind), trim(sense)
     if kind: wordkind = kind
     elif sense: 
        results.setdefault(wordkind, []).append(sense)
  result = "%s - " % (term)
  for key in sorted(results.keys()): 
     if results[key]: 
        result += (key or '') + ' 1. ' + results[key][0]
        if len(results[key]) > 1: 
           result += ', 2. ' + results[key][1]
        result += '; '
  result = result.rstrip('; ')
  if result.endswith('-') and (len(result) < 30): 
     #phenny.reply('Sorry, no definition found in Encarta.')
     pass
  else: 
    phenny.reply(result)
    resultCounter(term, 1)
  searchCounter(term, -1)
  return

if __name__ == '__main__': 
   print __doc__.strip()
