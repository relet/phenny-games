#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sandwich.py - Phenny Sandwich Paker Module
Author: Thomas Hirsch, http://relet.net
"""

import random

action = chr(1)+"ACTION "
afin   = chr(1)

def sandwich(phenny, input): 
   topping = random.choice(('avocado','lettuce','tomato','mozzarella cheese','bacon','spam','peanut butter','bratwurst','cruelty-free PeTA-approved fake guinea-pig','digital','cucumber','tofu','-if slightly burnt-','recursive','banana','ice-cream','ham&jam','tuna','double cheese','olive','..erm.. just','self-made','generic','sand','witch','two-hander'))
   phenny.say(action+"offers "+input.nick+" a tasty "+topping+" sandwich."+afin)
sandwich.commands=["food","sandwich","sudo make sandwich","noms"]
sandwich.priority="low"

def botsnack(phenny, input): 
  phenny.say(random.choice([
    "Botsnack WHAT?",
    "I'd rather feed on your procrastinating soul.",
    chr(1)+"ACTION throws the botsnack into the hungry mindless crowd."+chr(1),
    chr(1)+"ACTION is not your puppy."+chr(1),
    "Huh? BRAAAINS?",
    "Is that even vegan?",
  ]))
botsnack.rule = r'(Shmulik[, :]*)?[Bb]otsnack[!.]?'
botsnack.priority="low"

def botsnackok(phenny, input): 
  try:
    food = input[:-1].split("tasty")[1].strip()
    if food:
      phenny.say(random.choice([
        chr(1)+("ACTION noms on the %s ... Tastes interesting." % food) + chr(1),
        "Food for the hungry soul!",
        "I don't care what the others say, but THAT's a good %s" % food,
        "om-nom.",
        "om-nom-nom.",
        "Yuck!",
        "That'll look great on my weight watchers chart.",
      ]))
  except:
    phenny.say("Hear hear.")
botsnackok.rule = chr(1)+r'ACTION offers Shmulik a tasty .*'
botsnackok.priority="low"

#def testsnack(phenny, input):
#  print input
#testsnack.rule = r'.*'

if __name__ == '__main__': 
   print __doc__.strip()
