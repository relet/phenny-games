#!/usr/bin/env python

import re, bz2, sys

RE_definition = re.compile("\{\{en-(?:noun|adj|adv|verb|intj|[pP]roper.noun|prep|det|pron|conj|interjection|cont|infl-noun|term).*?# ?(.*?)\n",re.DOTALL)

data = bz2.BZ2File("enwiktionary-20090505-pages-articles.xml.bz2","r")

wordlist = {}

def analyze(title,doc):
  if '{{en-' in doc:
    res = RE_definition.search(doc)
    if res:
      clue = res.group(1)
#      print clue
      clue = re.sub("&lt;.*?&gt;","",clue)
      clue = re.sub("'''(?P<word>.*?)'''","\g<word>",clue)
      clue = re.sub("''(?P<word>.*?)''","\g<word>",clue)
      clue = re.sub("\[\[Image.*?\]\]","",clue)
      clue = re.sub("\{\{(?P<word>.*?)\}\}","",clue)
      clue = re.sub("\[\[(?:[^\]]*?\|)?(?P<word>.*?)\]\]","\g<word>",clue)
      clue = re.sub("[\[\]].*","",clue)
      clue = re.sub("&[a-z]+?;","",clue)
      clue = clue.strip()
#      print title.upper(), clue
      wordlist[title]=clue

STATUS_NONE    = 0
STATUS_INPAGE  = 1
STATUS_INTEXT  = 2

status = STATUS_NONE
doc = ''

for line in data:
  if status == STATUS_INTEXT:
    if '</text>' in line:
      doc += line[0:-8]
      if not ":" in title:
        analyze(title, doc)
      doc = ''
      status = STATUS_NONE
    else:
      doc += line
  elif status == STATUS_INPAGE:
    if '<title>' in line:
      title = line[11:-9]
    if '<text' in line:
      status = STATUS_INTEXT
      doc += line[33:]
  elif line=='  <page>\n':
    status = STATUS_INPAGE

for entry in wordlist:
  print "?%s" % entry
  print "!%s" % wordlist[entry].strip()
