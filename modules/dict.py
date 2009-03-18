#!/usr/bin/env python
"""
dict.py - Phenny Dictionary Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web
from tools import deprecated

formuri = 'http://wordnetweb.princeton.edu/perl/webwn?s='

r_entry = re.compile(r'<li>(.*?)</li>')
r_striptags = re.compile(r'<.*?>')
r_word = re.compile(r'^[A-Za-z0-9\' -]+$')

def f_wordnet(phenny, input): 
   """Gives the definition of a word using Wordnet."""
   command = 'w'
   if not " " in input:
     phenny.msg(input.sender, input.nick + ": Mu.")
     return
   term = input.split(" ")[1]

   if input.sender != '#inamidst': 
      if not r_word.match(term): 
         msg = "Words must match the regexp %s" % r'^[A-Za-z0-9\' -]+$'
         return phenny.msg(input.sender, input.nick + ": " + msg)
      if ('--' in term) or ("''" in term) or ('  ' in term): 
        phenny.msg(input.sender, input.nick + ": That's not in WordNet.")
        return

   bytes = web.get(formuri + web.urllib.quote(term)) # @@ ugh!
   items = r_entry.findall(bytes)

   msg = ""
   for item in items: 
      text = r_striptags.sub('',item)
      msg += text+"; "
   
   if not items: 
      phenny.msg(input.sender, "I couldn't find '%s' in WordNet." % term)
   else:
      phenny.msg(input.sender, msg)
   return
f_wordnet.commands = ['dict']
f_wordnet.priority = 'low'

uri = 'http://encarta.msn.com/dictionary_/%s.html'
r_info = re.compile(
   r'(?:ResultBody"><br /><br />(.*?)&nbsp;)|(?:<b>(.*?)</b>)'
)

def dict(phenny, input): 
   word = input.group(2)
   word = urllib.quote(word.encode('utf-8'))

   def trim(thing): 
      if thing.endswith('&nbsp;'): 
         thing = thing[:-6]
      return thing.strip(' :.')

   bytes = web.get(uri % word)
   results = {}
   wordkind = None
   for kind, sense in r_info.findall(bytes): 
      kind, sense = trim(kind), trim(sense)
      if kind: wordkind = kind
      elif sense: 
         results.setdefault(wordkind, []).append(sense)
   result = input.group(2).encode('utf-8') + ' - '
   for key in sorted(results.keys()): 
      if results[key]: 
         result += (key or '') + ' 1. ' + results[key][0]
         if len(results[key]) > 1: 
            result += ', 2. ' + results[key][1]
         result += '; '
   result = result.rstrip('; ')
   if result.endswith('-') and (len(result) < 30): 
      phenny.reply('Sorry, no definition found.')
   else: phenny.say(result)
dict.commands = ['encarta']

if __name__ == '__main__': 
   print __doc__.strip()
