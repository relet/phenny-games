#!/usr/bin/env python
"""
ping.py - Phenny Sandwich Paker Module
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

if __name__ == '__main__': 
   print __doc__.strip()
