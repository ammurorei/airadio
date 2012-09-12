#!/usr/bin/env python

# IMPORTS
from mpd import (MPDClient, CommandError)
from random import choice, shuffle
from socket import error as SocketError
from sys import exit

import air_download
import time
import yaml
import os

## SETTINGS
##
HOST = 'boxysean.com'
PORT = '6600'
PASSWORD = False
WAIT_SECONDS = 5
CONFIG = yaml.load(open("air_download.conf", "r"))
DIRECTORY = CONFIG["destination_folder"]
JINGLE_FREQUENCY = 1
JINGLE_DIRECTORY = "download/jingles"
###


def mpd_connect(host, port, password=None):
  client = MPDClient()
  
  try:
    client.connect(host, port)
  except SocketError:
    raise
  
  if password:
    try:
      client.password(password)
    except CommandError:
      raise

  return client

def sameList(a, b):
  if len(a) is not len(b):
    return False 
  
  for i in range(len(a)):
    if "jingle" in a[i] and "jingle" in b[i]:
      continue
    elif not a[i] == b[i]:
      return False

  return True

jingles = os.listdir(JINGLE_DIRECTORY)
shuffle(jingles)

desired_order = sorted([f for f in os.listdir(DIRECTORY) if os.path.isfile(os.path.join(DIRECTORY, f))]) 

# add jingles
jingle_idx = 0
n_songs_after_jingles = len(desired_order) + len(desired_order)/JINGLE_FREQUENCY
for jingle_idx, j in enumerate(range(0, n_songs_after_jingles, JINGLE_FREQUENCY+1)):
  desired_order.insert(j, os.path.join("jingles", jingles[jingle_idx%len(jingles)]))

print ":::desired order:::"
print "\n".join(desired_order)

client = mpd_connect(HOST, PORT)

present_order = map(lambda x: x["file"], client.playlistinfo())

print ":::present order:::"
print "\n".join(present_order)

lists_are_same = sameList(desired_order, present_order)
print ":::is it okay now?:::", lists_are_same

if not lists_are_same:
  # store present song
  mpd_status = client.status()
  current_song = client.currentsong()

  if current_song and current_song["file"] in desired_order:
    next_song_on_new_list = (desired_order.index(current_song["file"])+JINGLE_FREQUENCY+1) % len(desired_order)
    next_song = (next_song_on_new_list / (JINGLE_FREQUENCY+1)) * (JINGLE_FREQUENCY+1)
  else:
    next_song = 0

  # remake list
  client.clear()
  client.update()
  time.sleep(5)
  for i in desired_order:
    print "[+] adding %s" % (i)
    client.add(i)

  # fast forward to next advertisement... (abrupt kill)
  client.play(next_song)

client.disconnect()

while True:
  new_files = air_download.ezrun()

  if new_files:
    print "new files found!", new_files
    client = mpd_connect(HOST, PORT)
    for filename in new_files:
      client.update()
      time.sleep(5) # allow for the update to happen

      # check if we should add a jingle now
      if (len(client.playlistinfo()) % (JINGLE_FREQUENCY+1)) == 0:
        jingle_idx = jingle_idx+1
        jingle = jingles[jingle_idx%len(jingles)]
        print "[+] add %s" % (jingle)
        client.add(os.path.join("jingles", jingle))

      print "[+] add %s" % (filename)
      client.add(filename) 
    client.disconnect()

  time.sleep(WAIT_SECONDS)

