#!/usr/bin/python

import argparse
import os
import subprocess
import re
import yaml

from collections import defaultdict

#
# Counts syllables in a word using a simple heuristic
#

def countSyllables( word ):

  # Discard paths
  if word.count( "/" ) > 1:
    return 0

  # Discard anything that does not look like a word
  if len( re.findall( "[A-Z|a-z]", word ) ) == 0:
    return 0
  
  # Handle short words
  if len( word ) <= 3:
    return 1

  word = word.upper()

  # Discard non-alphabetic characters
  word = re.sub( "[^A-Z]", "", word )

  # Discard trailing "es" and "ed"
  if word[-2:] == "ES" or word[-2:] == "ED":
    word = word[:-2]

  # Discard trailing "e", except where the ending is "le"
  if word[-1] == "E" and word[-2] != "L":
    word = word[:-2]

  # Remove all consecutive vowels
  word = re.sub( "([AEIOU])[AEIOU]+", "\\1", word )

  # Count remaining vowels
  syllables = sum( x in set( "AEIOU" ) for x in word )

  # Adjust count if word starts with "mc"
  if word[:2] == "MC":
    syllables = syllables + 1
  
  return syllables

#
# Calculates FRES (Flesch Reading Ease Score)
#

def calculateFRES( numSentences, numWords, numSyllables ):
  return   206.835 \
         - 1.015 * (numWords / numSentences ) \
         - 84.6 * ( numSyllables / numWords )

#
# Main
#

def main():

  #
  # Parse command-line arguments
  #

  parser = argparse.ArgumentParser( description="Analyses git commits for their readability" )

  parser.add_argument(  "-r",
                        "--repository",
                        help = "Path to git repository" )

  arguments = parser.parse_args()

  if arguments.repository:
    directory = arguments.repository
  else:
    directory = "."

  #
  # Process input directory
  #

  os.chdir( directory )

  log = subprocess.check_output( [ "git", "log",
                                   "--format=" + 
                                   "---%nAuthor: %an%nBody: >%n%w(76,2,2)'%B'" ] )

  log = log.decode( 'utf-8' )

  scores = defaultdict(list)

  for commit in yaml.load_all( log ):

    author = commit['Author']
    body   = commit['Body']

    # Don't count URIs
    body = re.sub( "http[s]?://\S+",
                   "",
                   body )

    words = body.split()

    numWords     = len(words)
    numSentences = body.count( "." ) + 1 # +1 because I am assuming
                                         # that each commit has a
                                         # single header line

    numSyllables = 0

    for word in words:
      numSyllables = numSyllables + countSyllables( word )

    score = calculateFRES( numSentences,\
                           numWords,\
                           numSyllables )

    scores[author].append( score )

  #
  # Process all scores
  #

  for author in sorted(scores):
    print( "Mean readibility value for " + author + ":",
           sum( scores[author] ) / len( scores[author] ) )

if __name__ == "__main__":
  main()
