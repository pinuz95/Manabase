#
#
#
#
#
#
# Warning: This program written by a non-professional programmer.
# This is not the best piece of software that was written today.
# Constructive criticism and updates welcome!
#
# --Chris
#
#
#
#

# We will use random.sample as our shuffler.
import random

# We will deep copy some dictionaries of lists.
from copy import deepcopy

# We need some square roots.
import math

# We will use re.split in the deck parser.
import re

# We will work with files and directories, so we need to use os.path() and shutil.copyfile()
import os
import shutil

# When we want to exit, we want to just use exit()
from sys import exit

# We will need to import datetime to time our trials.
from datetime import datetime

# Our topological sorting algorithm uses this.
from functools import reduce

# Get the most updated AllCards.json from mtgjson.com. Then we use it here.
import json
json_data = open('AllCards.json', encoding="utf8")
cardDatabase = json.load(json_data)
json_data.close()


class LineOfPlay:
    # A line of play is a dictionary that keeps track of a sequence of plays. For example,
    # a line of play in human terms would be "Turn 1 play island and pass; turn 2 play Mountain and Goblin Electromancer."
    # The things kept track of in a line of play are:
    # Plays: a sequence of sequences. Plays[0] shows the cards played on turn 0. Plays[1] shows the cards played on turn 1.
    # Hand: a list of cards still in your hand
    # Deck: a list of cards still remaining in the deck, in order

    def __init__(self, plays, hand, deck):
        self.plays = plays
        self.hand = hand
        self.deck = deck

    def __repr__(self):
        # A line of play is a list of plays, a sequence of your hand, and the cards in the deck.
        return 'Turns: '+str(len(self.plays))+' Plays: ' + self.plays.__repr__() + ' Hand: ' + self.hand.__repr__() + ' Deck: ' + self.deck.__repr__()

    def draw_card(self):
        # The things we can do with a line of play include "drawing a card":
        # Pop the first item out of the list and put it in your hand.
        card = self.deck.pop(0)
        self.hand.append(card)
        return card

    def turn(self):
        # Plays is a list of lists. The length of this list is the turn we are on.
        return len(self.plays)


class ManaBase:
    # A ManaBase is a dictionary of lands and what they do, in addition to some synthesized information about how to play the mana.
    # For example, we need to know that Temple of Epiphany is strictly better than Island, so if tapping Island for blue doesn't get us there, there is no reason to try tapping Temple of Epiphany for the same blue.
    # Additionally, we get a little optimization by just putting the simpler lands first in the list manaSourcesInOrder.
    # It also contains some spells that help the mana, like Satyr Wayfinder or Courser of Kruphix.
    def __init__(self, decklist):
        # This function should take a decklist and go through all the manaproducers creating a small database and its helpers.
        # For example, a Jeskai decklist might end up with the following manaDatabase:
        # manaDatabase['Island'] = ['{U}']   (not the string {U}, but the ManaPool object)
        # manaDatabase['Mountain'] = ['{R}']
        # manaDatabase['Temple of Epiphany'] = ['{U}','{R}']
        # manaDatabase['Flooded Strand'] = ['FetchU','FetchW']    (the string 'FetchU')
        # However, green decks might have mana dorks, so they and manarocks will live in here too:
        # manaDatabase['Elvish Mystic'] = ['{G}']
        # manaDatabase['Sol Ring'] = ['{2}']

        if debug['parseMana']:
            print('')
        if debug['parseMana']:
            print('Beginning Mana Parser.')

        manaDatabase = {}
        spellDatabase = {}  # Spells that do not directly create mana, but affect our mana.

        # Every lands database needs some basic lands.
        manaDatabase['Island'] = [ManaPool('{U}')]
        manaDatabase['Mountain'] = [ManaPool('{R}')]
        manaDatabase['Swamp'] = [ManaPool('{B}')]
        manaDatabase['Forest'] = [ManaPool('{G}')]
        manaDatabase['Plains'] = [ManaPool('{W}')]

        for card in decklist:
            if isLand(card) and card not in manaDatabase:
                if debug['parseMana']:
                    print('Parsing land:', card)
                manaDatabase[card] = []
                if 'text' in cardDatabase[cardName(card)]:
                    # Parse through the text looking for mana symbols. We don't want to start counting until after the tap symbol (see Nykthos, Shrine to Nyx).
                    # When we get to a { we start a new symbol; a } ends it.
                    currentsymbol = ''
                    flagAfterTapSymbol = False
                    for char in cardDatabase[cardName(card)]['text']:
                        if char == '{':
                            currentsymbol = '{'
                        elif char == '}':
                            # After we get to the tap symbol, it's time to start adding to the list.
                            if currentsymbol == '{T':
                                flagAfterTapSymbol = True
                            elif currentsymbol == '{1':
                                # Every land is currently assumed to tap for {1}, so skip it
                                pass
                            elif flagAfterTapSymbol:
                                manaDatabase[card].append(ManaPool(currentsymbol+char))
                        elif char == '.':
                            # Again, see the two tap symbols in Nykthos for why this is here. Many lands have multiple sentences, which are separate abilities.
                            flagAfterTapSymbol = False
                        else:
                            # This is useful if the mana cost is 15, so we don't end up adding 6 to the mana cost.
                            currentsymbol += char
                    # Parse through the text looking for "scry" or "fetch."
                    if 'scry' in cardDatabase[cardName(card)]['text']:
                        manaDatabase[card].append('scry')
                    # This mana confluence catcher is definitely going to cause some false positives, like Springleaf Drum; TODO
                    if 'any color' in cardDatabase[cardName(card)]['text']:
                        manaDatabase[card].append(ManaPool('{W}'))
                        manaDatabase[card].append(ManaPool('{U}'))
                        manaDatabase[card].append(ManaPool('{R}'))
                        manaDatabase[card].append(ManaPool('{B}'))
                        manaDatabase[card].append(ManaPool('{G}'))
                    if 'Search your library' in cardDatabase[cardName(card)]['text']:
                        if 'Plains' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchW')
                        if 'Swamp' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchB')
                        if 'Mountain' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchR')
                        if 'Island' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchU')
                        if 'Forest' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchG')
                        if 'basic land card' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('FetchBasic')
                    if 'enters the battlefield tapped unless you control' in cardDatabase[cardName(card)]['text']:
                        if 'Plains' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('Check_Plains')
                        if 'Island' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('Check_Island')
                        if 'Swamp' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('Check_Swamp')
                        if 'Mountain' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('Check_Mountain')
                        if 'Forest' in cardDatabase[cardName(card)]['text']:
                            manaDatabase[card].append('Check_Forest')

                if debug['parseMana']:
                    print('Parsed as ', manaDatabase[card])
            elif card not in manaDatabase:
                # Okay, we're going to try to find all the mana dorks, manarocks, and other cards that could affect our mana.
                if debug['parseMana']:
                    print('Parsing nonland card:', card)
                if card == 'Satyr Wayfinder':
                    spellDatabase['Satyr Wayfinder'] = ('Dig for a Land', 4)
                if card == 'Courser of Kruphix':
                    spellDatabase['Courser of Kruphix'] = 'Play Lands From Top of Library'
                elif 'text' in cardDatabase[cardName(card)]:
                    # Manadorks and rocks should have these phrases:
                    if '{T}: Add' in cardDatabase[cardName(card)]['text'] and 'to your mana pool' in cardDatabase[cardName(card)]['text']:
                        # Start one character after "{T}: Add" and go up to "to your mana pool" and see what we get.
                        manaDatabase[card] = []
                        startLocation = cardDatabase[cardName(card)]['text'].index('{T}: Add') + 9
                        endLocation = cardDatabase[cardName(card)]['text'].index(
                            'to your mana pool') - 1
                        manaToParse = cardDatabase[cardName(
                            card)]['text'][startLocation:endLocation]
                        if debug['parseMana']:
                            print(
                                card, 'appears to be a mana producer; now parsing the string "', manaToParse, '"')
                        # Split the mana phrase into parts, so Sylvan Caryatid gets ['one','mana','of','any','color'] and Noble Hierarch is ['{G}','{W}','or','{U}']
                        for symbol in manaToParse.split():
                            # This implementation creates false positive on "of any color that lands you control could produce" type cards; not sure there are any nonland cards that do this.
                            if symbol == 'any':
                                manaDatabase[card].append(ManaPool('{W}'))
                                manaDatabase[card].append(ManaPool('{U}'))
                                manaDatabase[card].append(ManaPool('{R}'))
                                manaDatabase[card].append(ManaPool('{B}'))
                                manaDatabase[card].append(ManaPool('{G}'))
                            else:
                                # If you pass nonsense to ManaPool, like '{H}', it doesn't error; it just gives you back 0 mana.
                                mana = ManaPool(symbol)
                                if mana != ManaPool('{0}'):
                                    manaDatabase[card].append(ManaPool(symbol))
                        if debug['parseMana']:
                            print('Parsed as ', manaDatabase[card])

        # Okay, now comes the mathy part. Suppose you are trying to cast Savage Knuckleblade (cost: RUG) and you have the following lands:
        # Sylvan Caryatid, Mana Confluence, Forest
        # The way a human handles this issue is they say "aha -- the Forest is only useful for Green, so I better tap the Forest for green and the others for something else."
        # The key optimization idea here is that if we need a green mana, we try using Forest for it, and we can't cast the spell, then there is no use trying to use Mana Confluence for the green.
        # We will use what is called a "topological sort" of the lands to stratify things this way. For example, in a deck with lots of weird lands, you might have:
        # Forest, Yavimaya Coast, Frontier Bivouac, Sandsteppe Citadel, Sylvan Caryatid.
        # With respect to green, these can be topologically sorted as follows: [Forest], [Yavimaya Coast, Sandsteppe Citadel], [Frontier Bivouac], [Sylvan Caryatid].
        # This means that if you have a land from one of the lists, you tried tapping it for green and everything still failed, then there is no use trying anything from a later list.

        # At the end of this, we will build a partial ordering of all the mana producers in the deck. This will allow us to choose mana sources intelligently in the future.

        def secondManaSourceIsBetter(card1, card2):
            coloredManaSymbols = ['{W}', '{U}', '{B}', '{R}', '{G}']
            # the second mana source is better if its set of colored mana symbols is strictly larger.
            symbolsInCard1 = [symbol for symbol in coloredManaSymbols if (
                ManaPool(symbol) in manaDatabase[card1])]
            symbolsInCard2 = [symbol for symbol in coloredManaSymbols if (
                ManaPool(symbol) in manaDatabase[card2])]
            # The second list of symbols is strictly larger if everything in #2 is in #1, and something in #2 is not in #1.
            return (all([symbol in symbolsInCard2 for symbol in symbolsInCard1]) and any([symbol not in symbolsInCard1 for symbol in symbolsInCard2]))

        manaSourcesBetterThan = {}
        for card in manaDatabase:
            # Just make a list of all the othercards that are better than card.
            manaSourcesBetterThan[card] = set(
                [othercard for othercard in manaDatabase if secondManaSourceIsBetter(card, othercard)])

        if debug['parseMana']:
            print('End of Mana Parser. Results below:')
        if debug['parseMana']:
            print('     Mana Database:', manaDatabase)
        if debug['parseMana']:
            print('Mana Partial Order:', manaSourcesBetterThan)

        # Then we can create a topological sort of the mana sources. This is an order to try the lands in.
        toposorted = toposort(manaSourcesBetterThan)
        # toposorted is a list of sets. We want to concatenate them into a list, and we don't care about the order inside the sets.
        manaSourcesInOrder = []
        for cohortofcards in toposorted:
            for card in cohortofcards:
                manaSourcesInOrder.append(card)
        manaSourcesInOrder.reverse()

        if debug['parseMana']:
            print('Order to try Lands:', manaSourcesInOrder)
        if debug['parseMana']:
            print('')

        self.manaDatabase = manaDatabase
        self.manaSourcesBetterThan = manaSourcesBetterThan
        self.manaSourcesInOrder = manaSourcesInOrder
        self.spellDatabase = spellDatabase


class ManaPool:
    # A mana pool is really an object, for example 1U + 2UR = 3UUR.
    # We will store this as a number, some blue, some red, and so on.
    # A mana cost like {3}{U}{U}{G} needs to be the thing that starts it.
    def __init__(self, manacost):
        # This implementation would completely fail for, say, Boros Reckoner -- but that's why it is called
        # a Mana Pool, and not a Mana Cost. This implementation should allow all possible Mana Pools. If you
        # pass a nonsense string in here, like {H}, then you should just get {0} back.
        self.colorless = 0
        self.blue = 0
        self.green = 0
        self.white = 0
        self.red = 0
        self.black = 0

        # Parse through the mana cost. When we get to a { we start a new symbol, a } ends it.
        currentsymbol = ''
        for char in manacost:
            if char == '{':
                currentsymbol = ''
            elif char == '}':
                if currentsymbol == 'U':
                    self.blue += 1
                elif currentsymbol == 'G':
                    self.green += 1
                elif currentsymbol == 'R':
                    self.red += 1
                elif currentsymbol == 'W':
                    self.white += 1
                elif currentsymbol == 'B':
                    self.black += 1
                elif currentsymbol == 'X':
                    # Oh no! I have no idea what to set X to. Apparently we'll go with zero.
                    pass
                elif is_int(currentsymbol):
                    self.colorless += int(currentsymbol)
            else:
                # This is useful if the mana cost is 15, so we don't end up adding 6 to the mana cost.
                currentsymbol += char

    def __repr__(self):
        # The initializer for a mana pool is something like the string '{3}{W}{W}{G}', so the string representation gives back a string like that.
        string = ''
        if self.colorless > 0:
            string += ('{' + str(self.colorless) + '}')
        for i in range(self.white):
            string += '{W}'
        for i in range(self.blue):
            string += '{U}'
        for i in range(self.black):
            string += '{B}'
        for i in range(self.red):
            string += '{R}'
        for i in range(self.green):
            string += '{G}'
        if string == '':
            return '{0}'
        return string

    def __iadd__(self, other):
        # This implements += for mana pools.
        self.colorless += other.colorless
        self.blue += other.blue
        self.green += other.green
        self.white += other.white
        self.red += other.red
        self.black += other.black
        return self

    def __add__(self, other):
        # This lets us add mana pools with just plus signs.
        thesum = ManaPool('{0}')
        thesum.colorless = self.colorless + other.colorless
        thesum.blue = self.blue + other.blue
        thesum.green = self.green + other.green
        thesum.white = self.white + other.white
        thesum.red = self.red + other.red
        thesum.black = self.black + other.black
        return thesum

    def __isub__(self, other):
        # This implements += for mana pools.
        self.colorless -= other.colorless
        self.blue -= other.blue
        self.green -= other.green
        self.white -= other.white
        self.red -= other.red
        self.black -= other.black
        if self.isValid():
            return self
        else:
            raise ArithmeticError('Cannot subtract these mana pools.')

    def __sub__(self, other):
        # This lets us remove mana from the mana pool.
        thediff = ManaPool('{0}')
        thediff.colorless = self.colorless - other.colorless
        thediff.blue = self.blue - other.blue
        thediff.green = self.green - other.green
        thediff.white = self.white - other.white
        thediff.red = self.red - other.red
        thediff.black = self.black - other.black
        if thediff.isValid():
            return thediff
        else:
            raise ArithmeticError('Cannot subtract these mana pools.')

    def __eq__(self, other):
        # Mana Pools are equal if they have the same type and the dictionaries underneath are the same.
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def isValid(self):
        return ((self.colorless >= 0) and (self.blue >= 0) and (self.green >= 0) and (self.white >= 0) and (self.black >= 0) and (self.red >= 0))


def cardName(card):
    """Basically we shouldn't ever look in the manaDatabase, spellDatabase, or cardDatabase
    without first removing any modifiers like (Tapped) from the card name.

    >>> print(cardName('(Tapped) Mountain'))
    Mountain
    """
    if len(card) > 9:
        if card[0:8] == '(Tapped)':
            return card[9:]
    return card


def manaSourcesAvailable(lineofplay, manaBase, this_turn):
    """Given a line of play and a manabase, we want to know which mana
    sources are available to tap for mana. The lineofplay knows which
    turn each land and spell was played, while the manaBase knows
    whether those lands and spells are actually mana producers.
    This function uses the global cardDatabase to look at card text.
    Inputs are a LineOfPlay object and a ManaBase object. Output is
    a list of card names that can be used for mana this turn.
    """

    # Make a list of available cards (so we dont count tapped lands on the turn they come out and don't count summoning-sick dudes.)
    availablecards = []
    for i in range(lineofplay.turn()):
        # most cards played are available for use. First add them all.
        for card in lineofplay.plays[i]:
            if cardName(card) in manaBase.manaDatabase:
                availablecards.append(cardName(card))

    # For the one(s) we just played this turn, check whether it is a tapped land or a summoning sick creature.
    if lineofplay.turn() >= this_turn:
        for cardplayedthisturn in lineofplay.plays[this_turn-1]:
            cardname = cardName(cardplayedthisturn)
            # The only way a land is not available is if the land is explicitly tapped because of Evolving Wilds, or if it has text that contains the word 'tapped' but it is not a shockland or a checkland.
            if isLand(cardname) and 'text' in cardDatabase[cardname] and cardname in availablecards:
                if 'tapped' in cardDatabase[cardname]['text'] and 'you may pay 2 life' not in cardDatabase[cardname]['text'] and 'unless you control' not in cardDatabase[cardname]['text']:
                    availablecards.remove(cardname)
            if cardname is not cardplayedthisturn and cardname in availablecards:
                if cardplayedthisturn[1:7] == 'Tapped':
                    availablecards.remove(cardname)

            # A creature is unusable if it entered play this turn as well. TODO: Dryad Arbor, I guess, ugh why
            if isCreature(cardname) and cardname in availablecards:
                if 'text' in cardDatabase[cardname]:
                    # Are there hasty mana guys? who knows. If there are, we will let them be available. Lol.
                    if 'Haste' not in cardDatabase[cardname]['text']:
                        availablecards.remove(cardname)
                else:
                    # Vanilla creatures are also summoning sick, so unavailable.
                    availablecards.remove(cardname)

    if debug['checkManaAvailability']:
        print('        Available mana sources in this line of play:', availablecards)
    return availablecards


def landCountInHand(lineofplay):
    """Takes a LineOfPlay object as input and counts how many lands are in it.
    Uses isLand() to look at the global card database.

    >>> print(landCountInHand(LineOfPlay([['Forest','Elvish Mystic']],['Mountain','Sol Ring','Griselbrand'],['Swamp','Swamp','Swamp'])))
    1
    >>> print(landCountInHand(LineOfPlay([['Forest','Elvish Mystic']],['Mountain','Dryad Arbor','Griselbrand'],['Swamp','Swamp','Swamp'])))
    2
    """
    hand = lineofplay.hand
    landsinhand = 0
    for card in hand:
        if isLand(card):
            landsinhand += 1
    return landsinhand


def toposort(data):
    """Dependencies are expressed as a dictionary whose keys are items
    and whose values are a set of dependent items. Output is a list of
    sets in topological order. The first set consists of items with no
    dependences, each subsequent set consists of items that depend upon
    items in the preceeding sets.

    >>> print('\\n'.join(repr(sorted(x)) for x in toposort({
    ...     2: set([11]),
    ...     9: set([11,8]),
    ...     10: set([11,3]),
    ...     11: set([7,5]),
    ...     8: set([7,3]),
    ...     }) ))
    [3, 5, 7]
    [8, 11]
    [2, 9, 10]

    """
    # This recipe was taken from http://code.activestate.com/recipes/578272-topological-sort/ on December 31, 2014.

    # Ignore self dependencies.
    for k, v in data.items():
        v.discard(k)
    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    # Add empty dependences where needed
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        # ordered is the set of items that do not have any dependencies.
        ordered = set(item for item, dep in data.items() if not dep)
        # if we don't have any, then we are done.
        if not ordered:
            break
        # okay, return this set of items with no dependencies.
        yield ordered
        # then remove the set of items with no dependencies from the dictionary entirely.
        data = {item: (dep - ordered)
                for item, dep in data.items()
                if item not in ordered}
    # if it loops around and everything gets destroyed, then we have a cyclic dependency.
    assert not data, "Cyclic dependencies exist among these items:\n%s" % '\n'.join(
        repr(x) for x in data.items())


def comb(n, k):
    """Simple combinations function, the number of ways to choose
    k objects from n given objects.

    >>> print(comb(7, 3))
    35
    >>> print(comb(7, 0))
    1
    """
    if is_int(n) and is_int(k):
        if k >= 0 and k <= n:
            return int(math.factorial(n) / (math.factorial(k) * math.factorial(n-k)))
        else:
            return 0
    else:
        raise ValueError(
            'Can\'t take factorials of non-integers; you passed %n and %k to comb().' % (n, k))


def hypergeometricdistribution(draws, decksize, successes):
    """Given the number of cards you see, the number of cards in your deck,
    and the number of lands in the deck, returns the probability distribution
    of drawing various numbers of lands.

    >>> print(hypergeometricdistribution(7,60,24))
    {0: 0.02161452725911799, 1: 0.12104135265106074, 2: 0.26941462364268354, 3: 0.30870425625724157, 4: 0.1964481630727901, 5: 0.06933464579039651, 6: 0.012546269238262225, 7: 0.0008961620884473018}
    >>> print(hypergeometricdistribution(0,60,24))
    {0: 1.0}
    """
    # The probability of getting 2 lands in a 7 card hand given a 60-card deck of 24 lands is
    # (24 choose 2) lands times (36 choose 5) spells divided by (60 choose 7) ways to get those.
    distribution = {}
    for i in range(draws+1):
        distribution[i] = (comb(successes, i) * comb(decksize -
                                                     successes, draws - i) / comb(decksize, draws))
    return distribution


def baselinepercentages(decksize, landsindeck, onthedraw=False):
    """Given a deck size and the number of lands in the deck, this returns
    how often you should expect to keep various sized hands and how often
    you would expect to be able to cast various spells.

    >>> print(baselinepercentages(60, 24)[0])
    {4: 0.003032034748519207, 5: 0.03644270199141307, 6: 0.11662357449695596, 7: 0.8439016887631118}
    >>> print(baselinepercentages(60, 24)[1])
    {1: 0.9996141659673354, 2: 0.9928329519858352, 3: 0.8524984479014863, 4: 0.6548921060230839, 5: 0.45734589642095946}
    """
    probabilityofmulligan = {}
    # We mulligan 7 card hands if we draw 0, 1, 6, or 7 lands.
    probabilityofmulligan[7] = 0
    for i in [0, 1, 6, 7]:
        probabilityofmulligan[7] += hypergeometricdistribution(7, decksize, landsindeck)[i]
    # We mulligan 6 card hands if we draw 0, 1, 5, or 6 lands.
    probabilityofmulligan[6] = 0
    for i in [0, 1, 5, 6]:
        probabilityofmulligan[6] += hypergeometricdistribution(6, decksize, landsindeck)[i]
    # We mulligan 5 card hands if we draw 0, 5 lands.
    probabilityofmulligan[5] = 0
    for i in [0, 5]:
        probabilityofmulligan[5] += hypergeometricdistribution(5, decksize, landsindeck)[i]
    # We never mulligan 4 card hands.
    probabilityofmulligan[4] = 0

    # Now figure out what is the probability of keeping various-sized hands.
    probabilityofkeep = {}
    probabilityofkeep[7] = (1 - probabilityofmulligan[7])
    probabilityofkeep[6] = (1 - probabilityofmulligan[6])*probabilityofmulligan[7]
    probabilityofkeep[5] = (1 - probabilityofmulligan[5]) * \
        probabilityofmulligan[7]*probabilityofmulligan[6]
    probabilityofkeep[4] = (1 - probabilityofmulligan[4])*probabilityofmulligan[7] * \
        probabilityofmulligan[6]*probabilityofmulligan[5]
    # probabilityofkeep is now a dictionary that gives the probability of keeping x cards with y lands. probabilityofkeep is a probability distribution; it adds to 1.

    # Okay. Now the more complicated calculation, which is essentially the one from Karsten's article. We need to find
    # the probability that if we keep an n card hand, that after convertedManaCost-1 or convertedManaCost more draws, we can cast a spell that costs convertedManaCost.
    # Since we only keep good hands, the probabilities aren't independent and we have to go back to the hypergeometric distribution.
    wekept = {}
    wekept[(7, 2)] = hypergeometricdistribution(7, decksize, landsindeck)[2]
    wekept[(7, 3)] = hypergeometricdistribution(7, decksize, landsindeck)[3]
    wekept[(7, 4)] = hypergeometricdistribution(7, decksize, landsindeck)[4]
    wekept[(7, 5)] = hypergeometricdistribution(7, decksize, landsindeck)[5]
    wekept[(6, 2)] = hypergeometricdistribution(
        6, decksize, landsindeck)[2] * probabilityofmulligan[7]
    wekept[(6, 3)] = hypergeometricdistribution(
        6, decksize, landsindeck)[3] * probabilityofmulligan[7]
    wekept[(6, 4)] = hypergeometricdistribution(
        6, decksize, landsindeck)[4] * probabilityofmulligan[7]
    wekept[(5, 1)] = hypergeometricdistribution(5, decksize, landsindeck)[
        1] * probabilityofmulligan[7] * probabilityofmulligan[6]
    wekept[(5, 2)] = hypergeometricdistribution(5, decksize, landsindeck)[
        2] * probabilityofmulligan[7] * probabilityofmulligan[6]
    wekept[(5, 3)] = hypergeometricdistribution(5, decksize, landsindeck)[
        3] * probabilityofmulligan[7] * probabilityofmulligan[6]
    wekept[(5, 4)] = hypergeometricdistribution(5, decksize, landsindeck)[
        4] * probabilityofmulligan[7] * probabilityofmulligan[6]
    wekept[(4, 0)] = hypergeometricdistribution(4, decksize, landsindeck)[0] * \
        probabilityofmulligan[7] * probabilityofmulligan[6] * probabilityofmulligan[5]
    wekept[(4, 1)] = hypergeometricdistribution(4, decksize, landsindeck)[1] * \
        probabilityofmulligan[7] * probabilityofmulligan[6] * probabilityofmulligan[5]
    wekept[(4, 2)] = hypergeometricdistribution(4, decksize, landsindeck)[2] * \
        probabilityofmulligan[7] * probabilityofmulligan[6] * probabilityofmulligan[5]
    wekept[(4, 3)] = hypergeometricdistribution(4, decksize, landsindeck)[3] * \
        probabilityofmulligan[7] * probabilityofmulligan[6] * probabilityofmulligan[5]
    wekept[(4, 4)] = hypergeometricdistribution(4, decksize, landsindeck)[4] * \
        probabilityofmulligan[7] * probabilityofmulligan[6] * probabilityofmulligan[5]
    # wekept is now a dictionary that gives the probability of keeping x cards with y lands. wekept is a probability distribution; it adds to 1.

    # Now we want to evaluate the probability of casting a specific spell in our deck. So we don't care about all these hands -- just the ones with our spell.
    # If the hand has k spells in it and 4 of our N spells in the deck are the spell we care about, then the probability is hypergeo again.
    wekeptourspell = {}
    probability_we_have_our_spell = 0
    for (cards_in_hand, lands_in_hand) in wekept:
        our_spell_is_here = 0
        for number_of_draws_of_our_spell in range(1, cards_in_hand - lands_in_hand + 1):
            our_spell_is_here += hypergeometricdistribution(
                cards_in_hand - lands_in_hand, decksize - landsindeck, 4)[number_of_draws_of_our_spell]
        probability = wekept[(cards_in_hand, lands_in_hand)] * our_spell_is_here
        probability_we_have_our_spell += probability
        wekeptourspell[(cards_in_hand, lands_in_hand)] = probability
    # Now we have figured out the total probability of drawing our spell, and the way those draws were distributed among various hand types.

    # Now we can make the probability distribution of what our hand looks like ASSUMING we have our spell in hand.
    for (cards_in_hand, lands_in_hand) in wekeptourspell:
        wekeptourspell[(cards_in_hand, lands_in_hand)] = wekeptourspell[(
            cards_in_hand, lands_in_hand)] / probability_we_have_our_spell
    # wekeptourspell should now be a probability distribution, so it should add to 1.

    # Given that we kept a hand with a certain number of cards and a certain number of lands, we want to know if we can cast spells on time.
    castontime = {}
    failtocastontime = {}
    for convertedManaCost in range(1, 5+1):
        castontime[convertedManaCost] = 0
        failtocastontime[convertedManaCost] = 0
        additional_cards_to_draw = convertedManaCost - 1
        if onthedraw:
            additional_cards_to_draw += 1
        for (handsize, landsinhand) in wekeptourspell:
            # We need to draw at least lands_needed more lands in the next additional_cards_to_draw draws.
            lands_needed = convertedManaCost - landsinhand
            # print('Starting with',handsize,'cards of which',landsinhand,'are lands, we need',lands_needed,'more lands in the next',additional_cards_to_draw,'to cast our',convertedManaCost,'mana spell on time.')
            if lands_needed > 0:
                # We need at least convertedManaCost-landsinhand and at most additional_cards_to_draw lands in the next additional_cards_to_draw cards.
                for additionallands in range(lands_needed, additional_cards_to_draw + 1):
                    castontime[convertedManaCost] += wekeptourspell[(handsize, landsinhand)] * hypergeometricdistribution(
                        additional_cards_to_draw, decksize - handsize, landsindeck - landsinhand)[additionallands]
                for additionallands in range(0, lands_needed):
                    failtocastontime[convertedManaCost] += wekeptourspell[(handsize, landsinhand)] * hypergeometricdistribution(
                        additional_cards_to_draw, decksize - handsize, landsindeck - landsinhand)[additionallands]
            else:
                castontime[convertedManaCost] += wekeptourspell[(handsize, landsinhand)]

    return probabilityofkeep, castontime


def isLand(card):
    """Takes a string, looks it up in the global card database, and sees
    if 'Land' is in its list of types. Returns boolean True/false.


    >>> print(isLand('Dryad Arbor'))
    True
    >>> print(isLand('Birds of Paradise'))
    False
    >>> print(isLand('dRyAd ArBoR'))
    False
    """
    if card in cardDatabase:
        return ('Land' in cardDatabase[cardName(card)]['types'])
    else:
        return False


def isCreature(card):
    """Takes a string, looks it up in the global card database,	and sees
    if 'Creature' is in its list of types. Returns boolean True/false.

    >>> print(isCreature('Dryad Arbor'))
    True
    >>> print(isCreature('Birds of Paradise'))
    True
    >>> print(isCreature('dRyAd ArBoR'))
    False
    """
    if card in cardDatabase:
        return ('Creature' in cardDatabase[cardName(card)]['types'])
    else:
        return False


def is_int(s):
    """ Takes any object, tries to convert it to int. Returns True if that
    works, and False if we get a ValueError.

    >>> print(is_int('-8'))
    True
    >>> print(is_int('-8.0'))
    False
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def spacing(turn, lineOfPlayCounter):
    """Provides the spacing to put before text that is printed for the user during
    slowmode. The primary purpose of this is to provide indentation so that
    the branching tree of lines of play is not completely impossible to follow.

    >>> print(spacing(LineOfPlay([['Forest','Elvish Mystic'],['Swamp']],['Mountain','Sol Ring','Griselbrand'],['Swamp','Swamp','Swamp']).turn(), 143))
      143: |  |
    """
    return format(lineOfPlayCounter, '>5')+': '+'|  '*turn


def displayWithPlays(string, lineofplay):
    """We want to display a string, but also move over to the right and display the
    plays so far, justified. This means we need to depend on the string's length.

    >>> print(displayWithPlays('Hello there!',LineOfPlay([['Forest','Elvish Mystic'],['Swamp']],['Mountain','Sol Ring','Griselbrand'],['Swamp','Swamp','Swamp'])))
    Hello there!                                                                                                                                 Plays: [['Forest', 'Elvish Mystic'], ['Swamp']]
    """
    return string + ' '*(140 - len(string)) + ' Plays: '+str(lineofplay.plays)


def checkManaAvailability(symbolsToAcquire, manaBase, manaSourcesAvailable, urborgIsOut):
    """Input is the list of mana symbols we want to create in order, the manabase
    we are working with, and the mana sources that are available to tap for mana.
    Returns either True or False depending on whether we can make those mana symbols.
    When passing mana symbols to this list, make sure the colorless symbol appears last.

    This function calls itself recursively to emulate a human's decisionmaking
    when trying to tap mana. For example, when trying to use the following mana
    sources to create WRGU:	Forest, Temple of Epiphany, Island, Temple of Triumph, call
       checkManaAvailability(['{U}','{G}','{R}','{W}'],ManaBase(decklist),['Forest', 'Temple of Triumph', 'Temple of Epiphany', 'Island'], False)
    This function first tries to tap land for {U} by trying an Island. It knows to
    try the Island first (thanks to manaSourcesInOrder) and it knows that if tapping
    Island for {U} fails, there is no use trying to tap Temple of Epiphany for {U}
    (thanks to manaSourcesBetterThan). It then calls itself with the easier requirement:
       checkManaAvailability(['{G}','{R}','{W}'],ManaBase(decklist),['Forest', 'Temple of Triumph', 'Temple of Epiphany'], False)
    Next it taps Forest for {G}, then calls:
       checkManaAvailability(['{R}','{W}'],ManaBase(decklist),['Temple of Triumph', 'Temple of Epiphany'], False)
    Now it taps Temple of Triumph for {R} and calls:
       checkManaAvailability(['{W}'],ManaBase(decklist),['Temple of Epiphany'], False)
    which returns False. But because the temples are not strictly better than each other, it goes back
    and tries tapping Temple of Epiphany for the R instead, ending with
       checkManaAvailability(['{W}'],ManaBase(decklist),['Temple of Triumph'], False)
    which returns True.
    """
    if debug['checkManaAvailability']:
        print('         Trying to acquire', symbolsToAcquire, 'with', manaSourcesAvailable)

    # TODO: Some things like Nykthos or Sol Ring might make more than one mana; this treats them as making 1!
    convertedManaCost = 0
    for symbol in symbolsToAcquire:
        if is_int(symbol):
            convertedManaCost += int(symbol)
        else:
            convertedManaCost += 1
    if convertedManaCost > len(manaSourcesAvailable):
        if debug['checkManaAvailability']:
            print('         Thats not possible with this few sources.')
        return False

    # We return true if there is only one symbol to acquire and we can do it.
    if len(symbolsToAcquire) == 1:
        lastsymbol = symbolsToAcquire[0]

        # TODO: Some things like Nykthos or Sol Ring might make more than one mana.
        if is_int(lastsymbol):
            if int(lastsymbol) <= len(manaSourcesAvailable):
                if debug['checkManaAvailability']:
                    print('         Success! The last symbol was',
                          lastsymbol, 'and we had enough left.')
                return True
            else:
                if debug['checkManaAvailability']:
                    print('         Failure! The last symbol was',
                          lastsymbol, 'and we didnt have enough left.')
                return False
        elif any([(ManaPool('{'+lastsymbol+'}') in manaBase.manaDatabase[cardName(card)]) for card in manaSourcesAvailable]) or (lastsymbol is 'B' and urborgIsOut and len(manaSourcesAvailable) > 0):
            if debug['checkManaAvailability']:
                print('         Success! The last symbol was', lastsymbol, 'and we found it.')
            return True
        else:
            if debug['checkManaAvailability']:
                print('         Failure! The last symbol was',
                      lastsymbol, 'and we couldnt find it.')
            return False
    else:
        nextSymbol = symbolsToAcquire[0]

        manaSourcesTried = []
        # We need to try a variety of mana sources to acquire this mana. We'll try in the order of the list manaSourcesInOrder.
        for manaSource in manaBase.manaSourcesInOrder:
            if manaSource in manaSourcesAvailable:
                # Okay! We will try this -- but here is the thing. We don't try it if it is better than something we already tried.
                # This is the key optimization. If we tried using "Forest" for {G} and failed, then it is pointless to try using "Temple of Abandon" for the same {G}.
                if not any([manaSource in manaBase.manaSourcesBetterThan[manaSourceTried] for manaSourceTried in manaSourcesTried]):
                    if ManaPool('{'+nextSymbol+'}') in manaBase.manaDatabase[cardName(manaSource)] or (nextSymbol is 'B' and urborgIsOut):
                        # It's possible to use this card to satisfy this symbol, so we'll try it.
                        manaSourcesTried.append(manaSource)
                        newsymbolsToAcquire = list(symbolsToAcquire)
                        symbolRemoved = newsymbolsToAcquire.pop(0)
                        newmanaSourcesAvailable = list(manaSourcesAvailable)
                        newmanaSourcesAvailable.remove(manaSource)
                        if debug['checkManaAvailability']:
                            print('            With this try we have tried', manaSourcesTried, 'for', nextSymbol,
                                  '- removing source', manaSource, 'for', nextSymbol, ': remaining sources', newmanaSourcesAvailable)
                        # The only way this ends is if we find a path through this tree that satisfies the final symbol. If so, we win!
                        if checkManaAvailability(newsymbolsToAcquire, manaBase, newmanaSourcesAvailable, urborgIsOut):
                            return True
                else:
                    if debug['checkManaAvailability']:
                        print('            So far we tried', manaSourcesTried, 'for',
                              nextSymbol, '- no point trying', manaSource, 'for', nextSymbol)
        # If we get here, then I guess we didn't make it.
        if debug['checkManaAvailability']:
            print('         Failure! We couldnt get', symbolsToAcquire, 'from', manaSourcesAvailable)
        return False

########################################################


def userInterface():

    # Let's ask the user what they want to do for once.
    print('Welcome to Manabase!')
    print('')

    # Go see how many decks we have available.
    deckdirectory = os.listdir('decks/')
    numberofdecks = len(deckdirectory)

    if numberofdecks == 0:
        exit('You don\'t seem to have any decks in the /decks/ subdirectory. Go ahead and put at least one decklist in there as a text file, with one card per line. Each line could be like "4x Geist of Saint Traft".')

    print('You have', numberofdecks, 'decks on file. What would you like to do?')
    print('   0) Run one trial of one of those decks in slow motion to watch it happen.')
    print('   1) Run many trials of one of those decks.')
    print('   2) Run many trials of all of those decks (takes lots of time!)')
    print('   3) Look at the results in some way.')
    print('   4) See benchmarks for good manabases of various sizes.')
    print('  -1) Exit.')
    print('')

    whatToDo = (input('>>> '))

    print('')

    def chooseDeckAndGo(mode):
        for (i, deckfile) in enumerate(deckdirectory):
            print(format(i, '>4')+') '+deckfile)

        print('')
        whichDeck = int(input('>>> '))
        print('')

        for (i, deckfile) in enumerate(deckdirectory):
            if whichDeck == i:
                if mode is 'SingleTrial':
                    print('Great, we\'ll run one trial of', deckfile, 'in slow mode.')
                    trials = 1
                else:
                    print('Great, we\'ll run trials of', deckfile,
                          ' -- how many trials (recommend 10000 depending on computer)?')
                    print('')
                    trials = int(input('>>> '))

                print('')
                print('And how many turns would you like to go out (recommend 5, don\'t go crazy here.)?')
                print('')
                maxturns = int(input('>>> '))
                print('')

                # We are returning a list of decksToRun, maxturns, trials, onthedraw, mulligans
                return [deckdirectory[whichDeck]], maxturns, trials, False, True

        # If we get here, the input was invalid.
        print('Not sure which deck you are talking about, so we\'re going to have to start from the beginning. Sorry!')
        print('')
        return userInterface()

    if whatToDo == '0':
        # We need to choose the deck to use.
        print('Okay, we\'ll run one trial on one of those decks. Which deck?')
        return chooseDeckAndGo('SingleTrial')

    if whatToDo == '1':
        # We need to choose the deck to use.
        print('Okay, we\'ll run some trials on one of those decks. Which deck?')
        return chooseDeckAndGo('MultiTrial')

    elif whatToDo == '2':
        print('Great, we\'ll run trials of all of those decks -- how many trials (recommend 10000 depending on computer)?')
        print('')
        trials = int(input('>>> '))
        print('')
        print('And how many turns would you like to go out (recommend 5, don\'t go crazy here.)?')
        print('')
        maxturns = int(input('>>> '))
        print('')
        return deckdirectory, maxturns, trials, False, True

    elif whatToDo == '3':

        print('Okay, how do you want to see the results?')

        print('  1a) One deck, Text.')
        print('  1b) One deck, HTML.')
        print('  1c) One deck, Write an HTML File.')
        print('  1d) One deck, Reddit Markdown.')
        print('  2a) All decks, Text Format.')
        print('  2b) All decks, HTML Format.')
        print('  2c) All decks, Write HTML Files.')
        print('  2d) All decks, Reddit Markdown.')
        print('   3) Compare some decks that share spells, Reddit Markdown.')

        print('')

        whatToDo = ''
        while whatToDo not in ['1a', '1b', '1c', '1d', '2a', '2b', '2c', '2d', '3']:
            whatToDo = (input('>>> '))

        print('')

        if len(whatToDo) >= 2:
            if whatToDo[1] in ['a', 'A']:
                displayformats = ['text', 'print']
            if whatToDo[1] in ['b', 'B']:
                displayformats = ['html', 'print']
            if whatToDo[1] in ['c', 'C']:
                displayformats = ['html', 'file']
            if whatToDo[1] in ['d', 'D']:
                displayformats = ['reddit', 'print']

        if whatToDo[0] == '1':
            displayAllTheDecks = False
            print('Okay, let\'s look at the cumulative results of one of the decks, formatted in ' +
                  ', '.join(displayformats)+'. Which deck?')
            for (i, deckfile) in enumerate(deckdirectory):
                print(format(i, '>4')+') '+deckfile)

            print('')
            whichDeck = int(input('>>> '))
            print('')
        elif whatToDo[0] == '2':
            whichDeck = '-1'
            displayAllTheDecks = True
        elif whatToDo == '3':
            print('We will compare some decks.')
            for (i, deckfile) in enumerate(deckdirectory):
                print(format(i, '>4')+') '+deckfile)

            print('')
            whichDecks = input(
                'Which ones (enter a list with no spaces, e.g. 4,5,8,3)? >>> ').split(',')
            print('')

            decks_to_compare = []
            for (i, deckfile) in enumerate(deckdirectory):
                if str(i) in whichDecks:
                    decks_to_compare.append(deckfile)

            compareDecks(decks_to_compare)

            print('')

            return userInterface()

        for (i, deckfile) in enumerate(deckdirectory):
            if whichDeck == i or displayAllTheDecks:
                parseddraws, parsedcasts, parsedmaxturns = parseResults(
                    'results/'+deckfile[:-4]+'-results.txt')
                print('')
                print('Processing results for deck: ', deckfile)
                if parseddraws is None:
                    print(
                        'Hmm; you don\'t have any results for this deck yet. Why not run some trials on it using other options first?')
                else:
                    displayResults(displaycasts=parsedcasts, displaydrawslist=parseddraws,
                                   displayformat=displayformats, deckfile=deckfile)

        # If we got this far, then we displayed everything we could.
        print('')
        return userInterface()
    elif whatToDo == '4':
        print('This tool uses the hypergeometric distribution to tell you the exact probability of casting certain spells on time assuming:')
        print('   The deck has all untapped lands that all count toward casting the spell.')
        print('   You mulligan normally, not prioritizing the spell.')
        print('   You end up with the spell in your opening hand.')
        print('')
        print('How many cards will be in your deck (ex: 60)?')
        print('')
        decksize = int(input('>>> '))
        print('')
        print('How many lands will be in your deck (ex: 24)?')
        print('')
        landsindeck = int(input('>>> '))
        print('')
        if landsindeck < 0 or decksize < 0 or landsindeck > decksize:
            print('Not sure why you typed in nonsense numbers -- did you put them in the wrong order?')
            print('')
            return userInterface()
        else:
            mulliganstats = baselinepercentages(decksize, landsindeck, onthedraw=False)[0]
            statsontheplay = baselinepercentages(decksize, landsindeck, onthedraw=False)[1]
            statsonthedraw = baselinepercentages(decksize, landsindeck, onthedraw=True)[1]
            print('************************************************************************')
            print('Stats for a', decksize, 'card deck that has', landsindeck, 'basic lands.')
            print('Mulligan strategy: we mulligan 7-card hands with 0, 1, 6, or 7 lands.')
            print('                   we mulligan 6-card hands with 0, 1, 5, or 6 lands.')
            print('                   we mulligan 5-card hands with 0 or 5 lands.')
            print('                   we never mulligan 4-card hands.')
            print('************************************************************************')
            print('')
            print('Our opening hand has    7 cards   6 cards   5 cards   4 cards:')
            print('                        '+'{:>6.1%}'.format(mulliganstats[7])+'    '+'{:>6.1%}'.format(
                mulliganstats[6])+'    '+'{:>6.1%}'.format(mulliganstats[5])+'    '+'{:>6.1%}'.format(mulliganstats[4])+'   ')
            print('')
            print('************************************************************************')
            print('')
            print('Spells cast on time   On the Draw         On the Play:   ')
            for convertedManaCost in range(1, 6):
                print('              convertedManaCost '+str(convertedManaCost)+':    '+'{:>6.1%}'.format(
                    statsonthedraw[convertedManaCost])+'              '+'{:>6.1%}'.format(statsontheplay[convertedManaCost]))
            print('')
            print('************************************************************************')
            print('')
            print('You can improve on this with scrylands or other incidental mana fixing.')
            print('You can improve on this with a more intelligent mulligan strategy.')
            print('You can get much lower than this by having a multicolored deck. :)')
            print('')
            print('************************************************************************')
            input('Press [Enter] to continue.')
            print('')

            return userInterface()

    elif whatToDo == '-1':
        exit('Bye!')

    else:
        print('Not sure what you meant there, so we\'re going to have to start from the beginning. Sorry!')
        print('')
        return userInterface()


def parseDecklist(deckfile):
    """Input is a path to a text file; output is a tuple of (deck, decklist).
    A deck is a list of cards in order; a decklist is a dictionary of cards
    and how many of that card are in the deck.

    This function tries hard to read any text file as long as each line is one
    card with two entries separated by the delimiter [ x\t]+. So, for
    example it splits
    2x Xathrid Necromancer		as  	'2','Xathrid Necromancer'
    10x   	xxx	  x  Forest 	as  	'10','Forest'

    It also successfully stops reading the decklist if it ever sees the word "Sideboard."
    """

    # This will return a tuple of deck, decklist

    decklist = {}

    if debug['parseDecklist']:
        print('Beginning Decklist Parser.')

    inputfile = open(deckfile)
    for line in inputfile:
        if debug['parseDecklist']:
            print('Parsing line:', line.strip())
        # Don't include sideboard cards :)
        if 'Sideboard' in line or 'sideboard' in line:
            break

        # Split one time, based on delimiters of space, the letter x, and tab -- that way we can parse '2x 			Flooded Strand' as ['2','Flooded Strand']
        words = re.split(r'[ x\t]+', line, 1)
        # Okay, now the lines we want to parse look like ['2','Flooded Strand']
        if len(words) == 2:
            if is_int(words[0]):
                if debug['parseDecklist']:
                    print('Parsed as', int(words[0]), 'of card', words[1].strip())
                decklist[words[1].strip()] = int(words[0])
            else:
                if debug['parseDecklist']:
                    print('   skipped.')
        else:
            if debug['parseDecklist']:
                print('   skipped.')
    inputfile.close()
    for card in decklist:
        if card not in cardDatabase:
            # TODO: Make capitalization friendly so people don't get frustrated by the 'Hero Of Iroas'
            print('Decklist error: card not found. Check capitalization, or download the most recent AllCards.json from MTGJSON?', card)
            exit('Decklist error; sorry!! Fix the decklist and run program again.')

    if sum(decklist.values()) not in [40, 60]:
        if debug['parseDecklist']:
            print('Warning: decklist not 40 or 60 cards.')

    if debug['parseDecklist']:
        print('Decklist Parsing Complete. Decklist Below:')
    if debug['parseDecklist']:
        print(decklist)

    # A deck is a list of cards, as opposed to a decklist which is a dictionary, so turn the dictionary into a list with multiplicity.
    deck = []
    for card in decklist:
        deck.extend([card]*decklist[card])

    return deck, decklist


def runTrials(decksToRun, maxturns, trials, onthedraw, mulligans):

    # decksToRun is a list of decks from a directory listing. maxturns and trials tell us how much work to do; onthedraw is True or False, mulligans is probably always True.
    # If we are running a single trial, we go into a special mode where things go slowly.
    global slowMode
    global slowModeWait
    # If slowModeWait ever becomes "skip", then we will not wait for keyboard input anymore even in slowmode.
    slowModeWait = ''

    if trials is 1:
        slowMode = True
    else:
        slowMode = False

    for deckfilename in decksToRun:

        # Strip off the extension on the file.
        deckname = deckfilename[:-4]
        deckfile = 'decks/'+deckfilename

        # A decklist is a dictionary where the key is the card name and the value is the number of copies. This should make importing easy.
        # The decklist parser takes a filename and tries to read it.
        deck, decklist = parseDecklist(deckfile)

        # We need to go through all the manaproducers in our deck and figure out what is going on with them.
        # The manaDatabase is a dictionary that tells us what each land does. manaSourcesBetterThan tells us that Temple of Epiphany is better than Island. manaSourcesInOrder ranks the mana sources so we try them in an efficient order (i.e. tap Island for blue, not Opulent Palace).
        manaBase = ManaBase(decklist)

        # We are going to be counting how many times we draw or cast each nonland card in the list. Starting off, we will want a 0 for each nonland card in the deck.
        initialCount = {}
        for card in decklist:
            if not isLand(card):
                initialCount[card] = 0

        # Draws is a dictionary; its keys are card names and its values are the number of times we saw this card in opening hands.
        draws = initialCount.copy()

        # casts[0] is a dictionary; its keys are card names and its values are the number of times we cast this card in Turn 1.
        # casts[1] is a dictionary; its keys are card names and its values are the number of times we cast this card by Turn 2.
        # etc. up to maxturns.
        casts = []
        for i in range(maxturns):
            casts.append(initialCount.copy())

        # handsizes is a dictionary; its keys are hand sizes and its values are the number of times we started with that hand size.
        handsizes = {}
        for i in range(4, 8):
            handsizes[i] = 0

        # Let's go!
        for trial in range(trials):
            lineOfPlayCounter = 0
            trialStartTime = datetime.now()

            if slowMode:
                print('Starting a run of deck '+deckname+'.')
                print('')
            else:
                if trial % 100 == 0:
                    print('Trial', trial, 'of deck', deckname, 'starting.')

            # Start by drawing a hand of 7.
            lineofplay = drawHand(7, deck, lineOfPlayCounter)

            # If we are considering mulligans, then we have to look at how many lands we have. This is Karsten's basic mulligan strategy for simulators.
            if mulligans:
                if landCountInHand(lineofplay) in [0, 1, 6, 7]:
                    if slowMode:
                        print('Mulligan hand of 7 cards since it has',
                              landCountInHand(lineofplay), 'lands:', lineofplay.hand)
                    lineofplay = drawHand(6, deck, lineOfPlayCounter)
                    if landCountInHand(lineofplay) in [0, 1, 5, 6]:
                        if slowMode:
                            print('Mulligan hand of 6 cards since it has',
                                  landCountInHand(lineofplay), 'lands:', lineofplay.hand)
                        lineofplay = drawHand(5, deck, lineOfPlayCounter)
                        if landCountInHand(lineofplay) in [0, 5]:
                            if slowMode:
                                print('Mulligan hand of 5 cards since it has',
                                      landCountInHand(lineofplay), 'lands:', lineofplay.hand)
                            lineofplay = drawHand(4, deck, lineOfPlayCounter)

            # When we decide to keep a hand, keep track of how large the hand was that we kept.
            handsize = len(lineofplay.hand)
            handsizes[handsize] += 1
            if debug['EachTrial']:
                print('Trial #', trial, 'kept opening hand of', handsize, 'cards:',
                      lineofplay.hand, 'top few:', lineofplay.deck[:maxturns])
            if slowMode:
                print('Kept an opening hand of', handsize, 'cards:', lineofplay.hand)
                if slowModeWait.lower() == 'skip':
                    print('[Enter] to continue or "skip" to be done. The top of the deck looks like: ' +
                          str(lineofplay.deck[:maxturns+1]))
                else:
                    slowModeWait = input(
                        '[Enter] to continue or "skip" to be done. The top of the deck looks like: '+str(lineofplay.deck[:maxturns+1]))

            # Okay, we've set up the line of play, now play it.
            caststhistrial, spellsthistrial = playHand(lineofplay, manaBase, maxturns, onthedraw)

            # Go through the spells we drew and increment draws.
            for spell in spellsthistrial:
                draws[spell] += 1
            # After we've played through lots of lines of play, we have some 1s and 0s in caststhistrial.
            # We add that to casts.
            for i in range(maxturns):
                for card in caststhistrial[i]:
                    casts[i][card] += caststhistrial[i][card]

            if debug['EachTrial']:
                print('   Trial #', trial, 'complete after scanning', lineOfPlayCounter,
                      'lines of play,', (datetime.now()-trialStartTime).total_seconds(), 's')

        storeResults(deckname, decklist, draws, casts)

        print('')
        print('****************************************** Text of what we just did: ******************************************')
        displayResults(displaycasts=casts, displaydrawsdictionary=draws, displayhandsizes=handsizes, displayformat=[
                       'text', 'print'], displayonthedraw=onthedraw, deckfile=deckfile)
        print('')
        print('***************************************************************************************************************')


def drawHand(handsize, deck, lineOfPlayCounter):
    """Given a handsize and a deck, this shuffles the deck then draws a hand
    of that many cards. It then returns a LineOfPlay object with the result.
    Mulligans handled elsewhere. Python's random.sample is the shuffler.
    """
    # Shuffle the deck. TODO: Is random.sample good enough? I'm not sure actually.
    currentdeck = random.sample(deck, len(deck))
    # Create a new line of play based on this deck.
    lineofplay = LineOfPlay([], [], currentdeck)

    # Draw an initial hand.
    for i in range(handsize):
        carddrawn = lineofplay.draw_card()
        if slowMode:
            print(spacing(lineofplay.turn(), lineOfPlayCounter)+'Drew a card:', carddrawn)

    return lineofplay


def playHand(lineofplay, manaBase, maxturns, onthedraw):
    """Given a line of play, a mana base, and a maximum number of turns, this
    function actually plays the hand out by initializing caststhistrial and
    deciding which spells we are going to worry about casting.
    """
    # In this trial, we only care about how many times we cast the spells in the opening hand.
    # spellsthistrial is the list of spells we care about.
    # caststhistrial[0] is a dictionary with keys: spells in this opening hand, values:0 or 1, whether we cast it or not on Turn 1.
    # caststhistrial[1] is a dictionary with keys: spells in this opening hand, values:0 or 1, whether we cast it or not on Turn 2.
    # etc, up to maxturns.
    global slowMode
    global slowModeWait

    spellsthistrial = []
    caststhistrial = []
    for i in range(maxturns):
        caststhistrial.append({})

    rampIsPossible = 0
    for manaproducer in manaBase.manaDatabase:
        if not isLand(manaproducer):
            rampIsPossible = 1
    if slowMode:
        print('')
        if rampIsPossible:
            print('Since ramp is possible in this deck, all spells in our opening hand will be tracked.')
        else:
            print('Since ramp is not possible and we are only going to turn '+str(maxturns)+', only spells up to convertedManaCost '+str(maxturns) +
                  ' will be tracked. Notice that we won\'t cast non-ramp spells at all if they weren\'t in the opening hand.')

        if slowModeWait.lower() == 'skip':
            print('[Enter] to continue or "skip" to be done. Notice that we won\'t cast non-ramp spells at all if they weren\'t in the opening hand.')
        else:
            slowModeWait = input(
                '[Enter] to continue or "skip" to be done. Notice that we won\'t cast non-ramp spells at all if they weren\'t in the opening hand.')

        print('')

    # If we have two copies of a spell in the opening hand, we don't need to check it twice as often, so use set.
    for card in set(lineofplay.hand):
        if not isLand(card):
            # Optimization: If our deck contains no ramp, we can ignore spells that are too expensive to ever cast.
            # If we are never going to play enough turns to cast this spell, just act like you never even drew it, to save time.
            if rampIsPossible or cardDatabase[cardName(card)]['convertedManaCost'] <= maxturns:
                spellsthistrial.append(card)
                for i in range(maxturns):
                    caststhistrial[i][card] = 0

    # Continue playing. During "continue playing," we check whether cards are playable and set caststhistrial to 1 when possible.
    # If we are on the draw, we tell playTurn to start the turn by drawing a card, otherwise not.
    lineOfPlayCounter = 0
    lineOfPlayCounter, caststhistrial = playTurn(
        lineofplay, manaBase, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns, drawacard=onthedraw)

    if slowMode:
        print('')
        if slowModeWait.lower() == 'skip':
            print('Trial complete.')
        else:
            slowModeWait = input('[Enter] to continue or "skip" to be done. Trial complete.')

    return caststhistrial, spellsthistrial


def playTurn(lineofplay, manaBase, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns, drawacard=True):
    """Given a line of play, this function plays the next turn. The
    sequence of a turn is: draw a card if needed, then try to cast spells,
    then make a land drop, then try to cast spells again, then do the next
    turn."""
    global slowMode
    global slowModeWait
    manaDatabase, spellDatabase = manaBase.manaDatabase, manaBase.spellDatabase
    this_turn = lineofplay.turn() + 1

    if slowMode:
        if slowModeWait.lower() == 'skip':
            print(displayWithPlays(spacing(this_turn, lineOfPlayCounter)+'Now starting turn ' +
                                   str(this_turn) + ' with hand: '+str(lineofplay.hand), lineofplay))
        else:
            slowModeWait = input(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                                  'Now starting turn '+str(this_turn)+' with hand: '+str(lineofplay.hand), lineofplay))

    ######################################################
    # Start by drawing a card, if we are supposed to.
    ######################################################
    if drawacard:
        carddrawn = lineofplay.draw_card()
        if slowMode:
            print(spacing(this_turn, lineOfPlayCounter)+'Drew a card:', carddrawn)

    ######################################################
    # Try casting spells before our land drop, in case the spells we cast open up new land drop options.
    ######################################################
    # linesofplay is a list of lines of play that we will update throughout the turn.
    # castSpells always at least returns the line of play where we didn't play a spell.
    # The easiest optimization to do is to break out of the loop if we have already cast every single spell we care about already by this turn.
    if 0 not in caststhistrial[this_turn-1].values():
        if slowMode:
            print(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                   'We have successfully cast everything by turn '+str(this_turn)+', so we\'re moving on now.', lineofplay))
        linesneedingalanddrop = []
    else:
        lineOfPlayCounter, caststhistrial, linesneedingalanddrop = castSpells(
            lineofplay, manaBase, this_turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns)

    ######################################################
    # Now make a land drop.
    ######################################################
    # The goal is to build a list of lines of play to pass on to the next turn.
    linesafterthelanddrop = []
    for line in linesneedingalanddrop:
        if line.turn() is not this_turn:
            print(line)
            exit('Wait, a line of play is stuck on the wrong turn number!')

        # The easiest optimization to do is to break out of the loop if we have already cast every single spell we care about already by this turn.
        if 0 not in caststhistrial[this_turn-1].values():
            if slowMode:
                print(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                       'We have successfully cast everything by turn '+str(this_turn)+', so we\'re moving on now.', lineofplay))
            break

        lineOfPlayCounter, newlinesofplay = playLand(
            line, this_turn, manaBase, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns)
        # Keep track of all these lines.
        linesafterthelanddrop.extend(newlinesofplay)

    # Now we'll make the list of lines of play to pass on to the next turn.
    linesafterthespellcast = []

    ######################################################
    # Now that we made a land drop, try casting spells over and over until nothing new happens.
    ######################################################
    def castSpellsUntilWeCant(lineofplay, manaBase, this_turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns):
        playsWeMadeBeforeGettingHere = lineofplay.plays[this_turn-1]
        lineOfPlayCounter, caststhistrial, newlinesofplay = castSpells(
            lineofplay, manaBase, this_turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns)
        if len(newlinesofplay) is 1 and newlinesofplay[0].plays[this_turn-1] == playsWeMadeBeforeGettingHere:
            # If we only got one line back and it didn't change, that means we are done.
            return lineOfPlayCounter, caststhistrial, newlinesofplay
        else:
            # If we did something, then we need to make a list and try casting more spells!
            linestoreturn = []
            for linetofollow in newlinesofplay:
                lineOfPlayCounter, caststhistrial, newlinesofplay2 = castSpellsUntilWeCant(
                    linetofollow, manaBase, this_turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns)
                linestoreturn.extend(newlinesofplay2)
            return lineOfPlayCounter, caststhistrial, linestoreturn

    for line in linesafterthelanddrop:

        # The easiest optimization to do is to break out of the loop if we have already cast every single spell we care about already by this turn.
        if 0 not in caststhistrial[this_turn-1].values():
            if slowMode:
                print(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                       'We have successfully cast everything by turn '+str(this_turn)+', so we\'re moving on now.', lineofplay))
            break

        lineOfPlayCounter, caststhistrial, newlinesofplay = castSpellsUntilWeCant(
            line, manaBase, this_turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns)
        # Keep track of all these lines of play in a list.
        for newline in newlinesofplay:
            linesafterthespellcast.append(newline)

    # Okay, we've now created all the branches of the tree, but we have a possible problem of duplicated lines of play that we can avoid.
    # For example, since we cast spells before lands and then again after lands, we are almost always going to have two of each line.
    linesofplay = []
    for line in linesafterthespellcast:
        # This line of play is new until we prove otherwise.
        thislineisnew = True
        for oldline in linesofplay:
            # We want to see if the lines are "the same" in the sense that the *set*s of plays and hand this turn are the same and the *list*s of the deck are the same.
            if set(oldline.plays[this_turn - 1]) == set(line.plays[this_turn - 1]) and oldline.deck == line.deck and oldline.hand == line.hand:
                thislineisnew = False
                break
        if thislineisnew:
            linesofplay.append(line)

    # Now we have a list of all the lines of play to pass on to the next turn. Let's do it (if there is another turn!).
    if this_turn < maxturns:
        for line in linesofplay:
            # Sanity check: All lines of play here should be on the next turn.
            if line.turn() is not this_turn:
                print(line)
                exit('Wait, this line of play is stuck on the wrong turn number')
            lineOfPlayCounter, caststhistrial = playTurn(
                line, manaBase, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns, drawacard=True)

    return lineOfPlayCounter, caststhistrial


def playLand(lineofplay, this_turn, manaBase, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns):
    """This function takes a line of play and returns a line of play counter and a list of new lines of play where the land drops have been resolved."""
    newlinesofplay = []

    # Make a list of lands in the hand.
    landstotry = [card for card in lineofplay.hand if isLand(card)]

    # If a Courser of Kruphix (or similar) has been played, then we can also play lands off the top of our deck.
    spell_allowing_play_from_top_of_deck = None
    if isLand(lineofplay.deck[0]):
        for play in lineofplay.plays:
            for spell in play:
                if cardName(spell) in manaBase.spellDatabase:
                    if manaBase.spellDatabase[cardName(spell)] == 'Play Lands From Top of Library':
                        spell_allowing_play_from_top_of_deck = spell
                        landstotry.append('(Top of Deck)')

    # Optimization: If all the cards we are checking on have already been cast OR if there are no lands to play, then we don't actually have to even play another land.
    # Notice that here, if this_turn is 3, then we are actually about to work on turn 3. So we want to check caststhistrial[3-1].
    if 0 in caststhistrial[this_turn-1].values() and landstotry != []:

        for card in set(landstotry):

            if card == '(Top of Deck)':
                playing_from_top_of_deck = True
                card = lineofplay.deck[0]
            else:
                playing_from_top_of_deck = False

            # If it is a fetchland, we'll want to make two lines of play for the two fetch options. TODO: Pay 1 life
            if 'FetchU' in manaBase.manaDatabase[cardName(card)] or 'FetchW' in manaBase.manaDatabase[cardName(card)] or 'FetchB' in manaBase.manaDatabase[cardName(card)] or 'FetchG' in manaBase.manaDatabase[cardName(card)] or 'FetchR' in manaBase.manaDatabase[cardName(card)] or 'FetchBasic' in manaBase.manaDatabase[cardName(card)]:
                # Figure out what our fetch options are.
                we_played_a_fetchland = True
                fetchoptions = []
                for fetchOption in manaBase.manaDatabase[cardName(card)]:
                    if fetchOption == 'FetchU':
                        fetchoptions.append(('subtypes', 'Island'))
                    elif fetchOption == 'FetchW':
                        fetchoptions.append(('subtypes', 'Plains'))
                    elif fetchOption == 'FetchB':
                        fetchoptions.append(('subtypes', 'Swamp'))
                    elif fetchOption == 'FetchG':
                        fetchoptions.append(('subtypes', 'Forest'))
                    elif fetchOption == 'FetchR':
                        fetchoptions.append(('subtypes', 'Mountain'))
                    elif fetchOption == 'FetchBasic':
                        fetchoptions.append(('supertypes', 'Basic'))
                    else:
                        continue

                # Here we have something like [('subtypes','Forest'),('subtypes','Mountain')]. If our deck has four distinct cards with subtype forest or mountain, go get them all.
                # Make a dictionary of all the valid targets. The key will be the card title, and the value will be the index of the LAST occurrence of the card in the deck.
                # Grabbing the last occurrence of the card is a good plan because otherwise fetching the top card of your deck in a "try all lines of play" situation makes every fetchland be like a courser fetchland.
                fetchtargets = {}
                for fetch in fetchoptions:
                    for i, target in enumerate(lineofplay.deck):
                        if fetch[0] in cardDatabase[cardName(target)]:
                            if fetch[1] in cardDatabase[cardName(target)][fetch[0]]:
                                if (not playing_from_top_of_deck) or (playing_from_top_of_deck and i != 0):
                                    fetchtargets[target] = i

                if slowMode:
                    print(spacing(this_turn, lineOfPlayCounter) +
                          'Have a fetch with possible targets', fetchtargets)

                we_cracked_a_fetchland = False
                for target in fetchtargets:
                    newlineofplay = deepcopy(lineofplay)
                    # Remove our card from the hand and away entirely (we don't have a graveyard).
                    if playing_from_top_of_deck:
                        # Pop the appropriate card from the deck and into play (this is us popping the fetchland off the top).
                        if slowMode:
                            print(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                                   'Playing a land off the top thanks to '+spell_allowing_play_from_top_of_deck))
                        newlineofplay.plays[this_turn -
                                            1].append(newlineofplay.deck.pop(fetchtargets[target]))
                        newlineofplay.deck.remove(card)
                    else:
                        # Pop the appropriate card from the deck and into play.
                        newlineofplay.plays[this_turn -
                                            1].append(newlineofplay.deck.pop(fetchtargets[target]))
                        newlineofplay.hand.remove(card)

                    # Shuffle the deck. Wait! No. If we shuffle the deck, we create a prescience problem where playing a fetch doubles your chances of a good topdeck. Without shuffling, we do the scry/fetch interaction wrong, but that is a much smaller error.
                    # newlineofplay.deck = random.sample(newlineofplay.deck, len(newlineofplay.deck))

                    # Check if anything is castable and cast it -- this increments caststhisturn and makes new lines of play for spells we know how to handle, then continues playing.
                    if 'FetchBasic' in manaBase.manaDatabase[cardName(card)]:
                        lineOfPlayCounter += 1
                        newlineofplay.plays[this_turn -
                                            1][-1] = '(Tapped) ' + newlineofplay.plays[this_turn-1][-1]
                        if slowMode:
                            print(displayWithPlays(spacing(this_turn, lineOfPlayCounter)+'Found a possible turn ' +
                                                   str(this_turn)+' land drop: '+card+' fetching a tapped '+target, newlineofplay))
                        newlinesofplay.append(newlineofplay)
                        we_cracked_a_fetchland = True
                    else:
                        lineOfPlayCounter += 1
                        if slowMode:
                            print(displayWithPlays(spacing(this_turn, lineOfPlayCounter)+'Found a possible turn ' +
                                                   str(this_turn)+' land drop: '+card+' fetching a '+target, newlineofplay))
                        newlinesofplay.append(newlineofplay)
                        we_cracked_a_fetchland = True
            else:
                we_played_a_fetchland = False
                we_cracked_a_fetchland = False
                lineOfPlayCounter += 1
                # Playing a non-fetchland is much easier.
                newlineofplay = deepcopy(lineofplay)
                if playing_from_top_of_deck:
                    card_to_play = newlineofplay.deck.pop(0)
                else:
                    i = newlineofplay.hand.index(card)
                    card_to_play = newlineofplay.hand.pop(i)

                # If the land that came into play was a checkland, then we need to do the check.
                list_of_types_to_check = [checkOption for checkOption in ['Check_Plains', 'Check_Island', 'Check_Swamp',
                                                                          'Check_Mountain', 'Check_Forest'] if checkOption in manaBase.manaDatabase[card_to_play]]
                if len(list_of_types_to_check) > 0:
                    comes_into_play_tapped = True
                    for checktext in list_of_types_to_check:
                        type_to_check = checktext[6:]
                        for play in newlineofplay.plays:
                            for land in play:
                                if type_to_check in cardDatabase[land]['subtypes']:
                                    comes_into_play_tapped = False
                    if comes_into_play_tapped:
                        card_to_play = '(Tapped) '+card_to_play

                if playing_from_top_of_deck:
                    newlineofplay.plays[this_turn-1].append(card_to_play)
                else:
                    newlineofplay.plays[this_turn-1].append(card_to_play)

                if slowMode:
                    print(displayWithPlays(spacing(this_turn, lineOfPlayCounter) +
                                           'Found a possible turn '+str(this_turn)+' land drop: '+card_to_play, newlineofplay))
                newlinesofplay.append(newlineofplay)

            # If we just played a scryland, then we need to scry to the bottom and cast spells. We only care about this if there are turns left.
            # Here is the thing. If our land drop for the turn was a fetchland and we have a Courser out, we actually get a little extra value in that we can choose to shuffle or not.
            # This is currently implemented as: if you fetch with a courser out, the fetchland gets a "Scry 1" added to it. This is not correct, but it is approximately correct.
            if this_turn < maxturns:
                if 'scry' in manaBase.manaDatabase[cardName(card)] or (we_played_a_fetchland and we_cracked_a_fetchland and playing_from_top_of_deck):
                    # If the land was a scryland, then we also need a line of play where we bottomed the top card.
                    newlineofplay2 = deepcopy(newlineofplay)
                    # Put the top card on the bottom of the deck.
                    newlineofplay2.deck = newlineofplay2.deck[1:] + newlineofplay2.deck[:1]
                    lineOfPlayCounter += 1
                    if slowMode:
                        print(displayWithPlays(spacing(this_turn, lineOfPlayCounter)+'Found a possible turn ' +
                                               str(this_turn)+' land drop: '+card+' and a scry to the bottom', newlineofplay2))
                    newlinesofplay.append(newlineofplay2)

    else:
        # All the spells were already cast, so just keep going on to later turns by not playing a land here.

        if slowMode:
            print(spacing(this_turn, lineOfPlayCounter) +
                  'Not making a land drop this turn (either because we don\'t have one, or because we don\'t need to)')
        # Also remember to continue this line of play (where you didn't play a land this turn).
        lineOfPlayCounter += 1
        newlineofplay = deepcopy(lineofplay)
        # Check if anything is castable and cast it -- this increments caststhisturn and makes new lines of play for spells we know how to handle, then continues playing.
        newlinesofplay.append(newlineofplay)

    return lineOfPlayCounter, newlinesofplay


def castSpells(lineofplay, manaBase, turn, spellsthistrial, caststhistrial, lineOfPlayCounter, maxturns):
    """When we have played a land for this turn already but need to update
    caststhistrial[turn-1] with the with the new spell cast numbers, we call
    castSpells. This returns the new lineOfPlayCounter and the new count
    of which spells have been cast by which turn as well as a list of new lines.

    This function is also the one that branches new lines of play in the situation
    where we could play either an Elvish Mystic or an Avacyn's Pilgrim turn 1.

    This function is called twice each turn -- once before land drop, and once after.
    """
    if turn is lineofplay.turn() + 1:
        prelanddrop = True
    elif turn is lineofplay.turn():
        prelanddrop = False
    else:
        print('This line of play is on the wrong turn:', lineofplay)
        exit('Bye')

    spellsToCast = []
    manaAlreadySpent = ''

    if prelanddrop:
        # Always pass on at least the line where we don't cast a spell, pre land drop.
        lineOfPlayCounter += 1
        newlineofplay = deepcopy(lineofplay)
        newlineofplay.plays.append([])
        if slowMode:
            print(spacing(turn, lineOfPlayCounter) +
                  'Making a line of play where we cast nothing before land drop.')
        linesofplay = [newlineofplay]
    else:
        linesofplay = []
        for spell in lineofplay.plays[turn - 1]:
            if 'manaCost' in cardDatabase[cardName(spell)]:
                manaAlreadySpent += cardDatabase[cardName(spell)]['manaCost']

    # This tells us which cards are available to tap for mana.
    manaSources = manaSourcesAvailable(lineofplay, manaBase, turn)

    # The only spells we are counting are opening hand spells. Those are stored in spellsthistrial. But since we are using some spells for mana, we need to try casting everything in hand or in opening hand.
    for card in set([spell for spell in lineofplay.hand if not isLand(spell)]).union(spellsthistrial):
        if card not in caststhistrial[turn-1] and cardName(card) not in manaBase.manaDatabase and cardName(card) not in manaBase.spellDatabase:
            # We don't need to care about non-manaproducing spells if they weren't in the opening hand.
            # TODO: Courser or card draw spells do matter.
            continue
        elif card in caststhistrial[turn-1] and cardName(card) not in manaBase.manaDatabase and cardName(card) not in manaBase.spellDatabase:
            if caststhistrial[turn-1][card] == 1:
                # We don't need to care about non-manaproducing spells if we already found a way to cast them earlier.
                # TODO: Courser or card draw spells do matter.
                continue
        elif card in caststhistrial[turn-1] and card not in lineofplay.hand:
            if caststhistrial[turn-1][card] == 1:
                # We also don't care about mana-producing spells that we cast that are already out of our hand.
                continue

        # Go to the card database to get the mana cost. Make sure you take into account the fact that we may have played some spells already this turn.
        manaCost = cardDatabase[cardName(card)]['manaCost'] + manaAlreadySpent

        # For now, X is always 0.
        newManaCost = manaCost.replace('{X}', '')

        symbolsToAcquire = re.split(r'[{} ]+', newManaCost[1:-1])

        # Sort the mana cost since it might look like {1}{G}{G}{2}{W}{W} which should be {3}{G}{G}{W}{W}
        colorless = 0
        for symbol in symbolsToAcquire:
            if is_int(symbol):
                colorless += int(symbol)
                symbolsToAcquire.remove(symbol)
        if colorless > 0:
            symbolsToAcquire.append(str(colorless))

        # If we accidentally killed the mana cost by removing X, make it zero.
        if symbolsToAcquire == []:
            symbolsToAcquire = ['0']

        # This function recursively tries to acquire all these symbols given these mana sources. If Urborg is in any of the plays, pass True in the urborg slot.
        if debug['checkManaAvailability']:
            print('         Starting the chain, trying to get',
                  symbolsToAcquire, 'from', manaSources)
        isCastable = checkManaAvailability(symbolsToAcquire, manaBase, manaSources, any(
            'Urborg, Tomb of Yawgmoth' in play for play in lineofplay.plays))

        if isCastable:
            if slowMode:
                print(spacing(turn, lineOfPlayCounter)+'Successfully paid cost for', card,
                      '... we found', manaCost, 'in', manaSources, 'on turn '+str(turn)+'.')
            # If the mana is doable, let's make sure we don't have any other requirements, like Chained to the Rocks:
            if card == 'Chained to the Rocks':
                if slowMode:
                    print(spacing(turn, lineOfPlayCounter) +
                          'Well, the mana is okay, but there are other requirements to check for '+card+'...')
                haveMountain = 0
                for play in lineofplay.plays:
                    for card2 in play:  # Technically an Elvish Mystic might be in here, but it's okay; I guess if we cast a Mountain Creature somehow, you could Chain to it.
                        if 'subtypes' in cardDatabase[cardName(card2)]:
                            if 'Mountain' in cardDatabase[cardName(card2)]['subtypes']:
                                if slowMode:
                                    print(spacing(turn, lineOfPlayCounter) +
                                          '*** We successfully cast a turn '+str(turn)+' '+card+'.')
                                # Okay, it's cool that the spell was castable, but if it isn't in our hand anymore, we don't want to return it.
                                if card in lineofplay.hand:
                                    spellsToCast.append(card)
                                # Again: only count spells that were in our opening hand.
                                if card in spellsthistrial:
                                    for i in range(turn, maxturns+1):
                                        caststhistrial[i-1][card] = 1
            else:
                # We aren't incrementing this; it is a flag 0 or 1.
                if slowMode:
                    print(spacing(turn, lineOfPlayCounter) +
                          '*** We successfully cast a turn '+str(turn)+' '+card+'.')
                # Okay, it's cool that the spell was castable, but if it isn't in our hand anymore, we don't want to return it.
                if card in lineofplay.hand:
                    spellsToCast.append(card)
                # Again: only count spells that were in our opening hand.
                if card in spellsthistrial:
                    for i in range(turn, maxturns+1):
                        caststhistrial[i-1][card] = 1

    weCouldNotCastAnythingInOurHand = True

    manaDatabase, spellDatabase = manaBase.manaDatabase, manaBase.spellDatabase

    # We don't actually want to cast very many spells. For now, the only ones we care about are in the manaDatabase.
    # TODO: Courser, Card Draw Spells
    for spell in spellsToCast:
        if cardName(spell) in manaDatabase or cardName(spell) in spellDatabase:
            # This one is a mana producer or somehow affects our mana, so make a new line of play where we cast this.
            if spell in lineofplay.hand:
                weCouldNotCastAnythingInOurHand = False
            newlineofplay = deepcopy(lineofplay)

            i = newlineofplay.hand.index(spell)
            if prelanddrop:
                newlineofplay.plays.append([newlineofplay.hand.pop(i)])
            else:
                newlineofplay.plays[newlineofplay.turn()-1].append(newlineofplay.hand.pop(i))

            if cardName(spell) in spellDatabase:
                # In theory we will map various cards to various effects in the ManaBase class at some point. For now, we've implemented "lands off the top" for wayfinder.
                if spellDatabase[cardName(spell)][0] == 'Dig for a Land':
                    numberOfCardsToLookAt = spellDatabase[cardName(spell)][1]
                    cardsWeAlreadyDrew = []
                    for i in range(numberOfCardsToLookAt):
                        if isLand(newlineofplay.deck[i]) and newlineofplay.deck[i] not in cardsWeAlreadyDrew:
                            # Make a new line of play where we put this land into our hand.
                            newlineofplay2 = deepcopy(newlineofplay)
                            landWeFound = newlineofplay2.deck.pop(i)
                            cardsWeAlreadyDrew.append(landWeFound)
                            newlineofplay2.hand.append(landWeFound)
                            # Put the rest of the cards in the graveyard.
                            for i in range(numberOfCardsToLookAt - 1):
                                x = newlineofplay2.deck.pop(0)
                            lineOfPlayCounter += 1
                            if slowMode:
                                print(displayWithPlays(spacing(
                                    turn, lineOfPlayCounter)+'Making a line of play where '+spell+' draws us a '+landWeFound, newlineofplay2))
                            linesofplay.append(newlineofplay2)
                    if slowMode:
                        print(spacing(turn, lineOfPlayCounter) +
                              '(The line below is the one where '+spell+' draws us nothing)')

            # Keep going, if we should.
            # Here, a land for turn has already been played, so if turn() is 4 and maxturns is 4, we actually don't want to play another turn.
            if newlineofplay.turn() <= maxturns:
                lineOfPlayCounter += 1
                if slowMode:
                    print(displayWithPlays(spacing(turn, lineOfPlayCounter) +
                                           'Making a line of play where we cast '+spell+' and remember we cast it.', newlineofplay))
                linesofplay.append(newlineofplay)

    if weCouldNotCastAnythingInOurHand and not prelanddrop:
        # Keep going without casting anything after our land drop ONLY if it was impossible to cast something. This implementation means we always
        # cast a mana guy if we can. Here, a land for turn has already been played, so if turn() is 4 and maxturns is 4, we actually don't want to play another turn.
        if turn < maxturns:
            lineOfPlayCounter += 1
            newlineofplay = deepcopy(lineofplay)
            if slowMode:
                print(spacing(turn, lineOfPlayCounter) +
                      'Making a line of play where we move on without casting anything after', newlineofplay.plays)
            linesofplay.append(newlineofplay)

    return lineOfPlayCounter, caststhistrial, linesofplay


def parseResults(resultsfile):
    """ This function reads lines of data like
    Elvish Mystic	12/14	11/12	12/12	12/12	12/12
    and interprets it as "in tests run so far, we have these results:
    We cast Turn 1 Mystic 12 times out of the 14 times we saw it in our opening hand
    We cast Turn 2 Mystic 11 times out of the 12 times we saw it in our opening hand
    etc.

    The reason these denominators could be different in this case is that someone
    apparently ran two trials that only did simulations out to one turn.
    """
    parseddraws = []
    parsedcasts = []

    if not os.path.isfile(resultsfile):
        return None, None, None

    results = open(resultsfile)
    for result in results:
        # Each line in this file is a card name, then a series of proportions -- tab delimited.
        # For example, Elvish Mystic	4/10 	6/10 	9/10 	10/10
        if debug['storeResults']:
            print('Trying to parse the results line', result.strip())

        # Start by splitting on tabs.
        resultsequence = result.split('\t')

        # We want a blank dictionary to fill in.
        parsedmaxturns = len(resultsequence) - 1
        for i in range(parsedmaxturns):
            if len(parseddraws) <= i:
                parseddraws.append({})
            if len(parsedcasts) <= i:
                parsedcasts.append({})

        # Get the card name out of the list first.
        card = resultsequence.pop(0)

        if debug['storeResults']:
            print('   Figured out it is a result of card "', card, '"')

        # Okay, now populate the right numbers.
        for (turn, fraction) in enumerate(resultsequence):
            numbers = fraction.split('/')

            parsedcasts[turn][card] = int(numbers[0].strip())
            parseddraws[turn][card] = int(numbers[1].strip())
            if debug['storeResults']:
                print('   The parsed data on', card, 'on turn', turn+1, 'is',
                      parsedcasts[turn][card], 'out of', parseddraws[turn][card])

    results.close()
    return parseddraws, parsedcasts, parsedmaxturns


def storeResults(deckname, decklist, draws, casts):
    """Given the name of the deck and the results of a series of trials,
    this function reads the old results file, combines the data from these
    trials, and writes the combined data to a file.
    """
    # Okay. draws is a dictionary with keys: spell names and with values: the number of times we drew this spell.
    # casts[0] is a dictionary; its keys are card names and its values are the number of times we cast this card in Turn 1.
    # casts[1] is a dictionary; its keys are card names and its values are the number of times we cast this card by Turn 2.
    # etc. up to maxturns.
    # handsizes is a dictionary; its keys are the numbers 4 through 7, and the values are the number of times we kept hands of that size.
    # onthedraw is a boolean that tells us play or draw.

    # The results would be stored in deckfile minus extension plus '-results.txt'
    resultsfile = 'results/'+deckname+'-results.txt'
    cacheddeckfile = 'results/'+deckname+'-cached.txt'

    if debug['storeResults']:
        print('Storing results in files', resultsfile, 'and', cacheddeckfile)

    # However, in the stored file, we need a different number of draws for each turn, in case you run data out to 5 turns once, then out to 7 turns later.
    # So, draws is a list of dictionaries like casts, described above.
    olddraws = []
    oldcasts = []

    # First we need to check if we have any stored results for this deck.
    if os.path.isfile(resultsfile):
        if debug['storeResults']:
            print('The results file already exists.')

        # If so, we need to make sure it's the same deck that we have stored results for.
        cacheddeck, cacheddecklist = parseDecklist(cacheddeckfile)
        if cacheddecklist != decklist:
            print('Warning: It looks like the stored results are for a different deck that used the same filename.')
            # If the deck changed, rename the old results so we don't lose them.
            # We want to rename the old results from something-results.txt to something-backup-1-results.txt
            backupnumber = 0
            while True:
                backupnumber += 1
                backupresultsfile = 'results/'+deckname+'-backup-'+str(backupnumber)+'-results.txt'
                backupcacheddeckfile = 'results/'+deckname + \
                    '-backup-'+str(backupnumber)+'-cached.txt'
                if debug['storeResults']:
                    print('Storing old results in files',
                          backupresultsfile, 'and', backupcacheddeckfile)
                if not os.path.isfile(backupresultsfile):
                    os.rename(resultsfile, backupresultsfile)
                    os.rename(cacheddeckfile, backupcacheddeckfile)
                    break
            print('Moved the old results to results/'+deckname+'-backup-' +
                  str(backupnumber)+'-results.txt to avoid losing them.')
            # Now if we moved the results file out of the way, we'd prefer to pretend it was never there. As a result, "if isfile(resultsfile)" will happen again.

    # First we need to check if we have any stored results for this deck.
    if os.path.isfile(resultsfile):
        # In this case, we can open the old results and store them.
        olddraws, oldcasts, oldmaxturns = parseResults(resultsfile)

        # Now that the old numbers are in place, make a new place to hold the new totals.
        totaldraws = []
        totalcasts = []
        for turn in range(max(maxturns, oldmaxturns)):
            totaldraws.append({})
            totalcasts.append({})
            if len(casts) > turn and len(oldcasts) > turn:
                # This is the case where this turn is valid for both old and new.

                # We will start by going through all the cards inthe olddraws.
                for card in olddraws[turn]:
                    if card in casts[turn]:
                        # This is the case where this turn is valid for both old and new and the card was drawn both times.
                        if debug['storeResults']:
                            print('   Both old and new data available for', card,
                                  'for turn', turn+1, '... adding the numbers.')
                        totaldraws[turn][card] = olddraws[turn][card] + draws[card]
                        totalcasts[turn][card] = oldcasts[turn][card] + casts[turn][card]

                    else:
                        # This is the case where this turn is valid for both old and new and the card was drawn in old, but not new.
                        if debug['storeResults']:
                            print('   Old data available for', card,
                                  'but not new data for turn', turn+1)
                        totaldraws[turn][card] = olddraws[turn][card]
                        totalcasts[turn][card] = oldcasts[turn][card]

                # Now pick up anything in draws that is not in olddraws.
                for card in draws:
                    if card not in olddraws[turn]:
                        # This is the case where this turn is valid for both old and new and the card was drawn in new, but not old.
                        if debug['storeResults']:
                            print('   New data available for', card,
                                  'but not old data for turn', turn+1)
                        totaldraws[turn][card] = draws[card]
                        totalcasts[turn][card] = casts[turn][card]

            elif len(casts) > turn and len(oldcasts) <= turn:
                # This is the case where this turn is valid for new but not old.
                for card in casts[turn]:
                    if debug['storeResults']:
                        print('   New data available for', card,
                              'but not old data for turn', turn+1)
                    totaldraws[turn][card] = draws[card]
                    totalcasts[turn][card] = casts[turn][card]

            elif len(casts) <= turn and len(oldcasts) > turn:
                # This is the case where this turn is valid for old but not new.
                for card in oldcasts[turn]:
                    if debug['storeResults']:
                        print('   Old data available for', card,
                              'but not new data for turn', turn+1)
                    totaldraws[turn][card] = olddraws[turn][card]
                    totalcasts[turn][card] = oldcasts[turn][card]

    else:
        # In this case, we will need to make a blank cached deckfile.
        shutil.copy2('decks/'+deckname+'.txt', cacheddeckfile)

        # Then use our current numbers (in globals draws and casts).
        totaldraws = []
        for i in range(maxturns):
            totaldraws.append(draws)
        totalcasts = casts

    # Output the new data to the file.
    with open(resultsfile, 'w') as f:
        for card in totaldraws[0]:
            stringtosave = card
            for turn in range(len(totaldraws)):
                stringtosave += '\t'
                stringtosave += str(totalcasts[turn][card])
                stringtosave += '/'
                stringtosave += str(totaldraws[turn][card])
            stringtosave += '\n'
            f.write(stringtosave)


def displayResults(displaycasts=None, displaydrawsdictionary=None, displaydrawslist=None, displayhandsizes=None, displayonthedraw=None, displayformat='text', deckfile=''):
    """ This function either displays or writes to a file the results of a series of trials.
    """
    # casts[0] is a dictionary; its keys are card names and its values are the number of times we cast this card in Turn 1.
    # casts[1] is a dictionary; its keys are card names and its values are the number of times we cast this card by Turn 2.
    # etc. up to maxturns.

    # draws might be passed to us as a straight-up dictionary of cards, or it might be a list of dictionaries in the same style as casts above.

    # handsizes is a dictionary; its keys are the numbers 4 through 7, and the values are the number of times we kept hands of that size.
    # onthedraw is a boolean that tells us play or draw.
    if displayonthedraw is True:
        drawplay = 'On the Draw.'
    elif displayonthedraw is False:
        drawplay = 'On the Play.'

    if displayonthedraw is not None and 'print' in displayformat:
        print('')
        print('Finished running', deckfile, '-', drawplay, 'Ran', trials, 'trials.')

    if displayhandsizes is not None and 'print' in displayformat:
        print('')
        for handsize in displayhandsizes:
            print('Kept', displayhandsizes[handsize], 'hands with', handsize,
                  'cards,', '{:>6.1%}'.format(displayhandsizes[handsize]/trials))

    # If we have been passed a dictionary of cards, then we can just iterate over that dictionary.
    # If we were instead passed a list of dictionaries of cards, with the list index representing the turn number, then just look at the first turn and iterate over those cards.
    if displaydrawslist is not None:
        cardstoiterate = displaydrawslist[0]
    else:
        cardstoiterate = displaydrawsdictionary

    # It would be nice for display purposes to sort these by convertedManaCost, and then alphabetically.
    sorted_cardstoiterate = []
    list_of_convertedManaCosts = list(
        set([cardDatabase[card]['convertedManaCost'] for card in cardstoiterate]))
    list_of_convertedManaCosts.sort()
    for convertedManaCost in list_of_convertedManaCosts:
        list_of_spells = [card for card in cardstoiterate if cardDatabase[card]
                          ['convertedManaCost'] == convertedManaCost]
        list_of_spells.sort()
        sorted_cardstoiterate.extend(list_of_spells)

    percents = {}
    # To justify the text, we need to know the max card length.
    maxcardlength = max([len(card) for card in cardstoiterate])

    # How many turns are we looking at here?
    displaymaxturns = len(displaycasts)

    if 'html' in displayformat:
        header = '<table><tr><th align=center>Card</th>\n'
        for i in range(displaymaxturns):
            header += '<th align=center width=100>Turn'+str(i+1)+'</th>'
        header += '\n</tr>\n'
    elif 'reddit' in displayformat:
        header = '\n Card '
        for i in range(displaymaxturns):
            header += ' | Turn '+str(i+1)
        header += '\n ---'
        for i in range(displaymaxturns):
            header += '|----'
    else:
        header = ''

    for card in sorted_cardstoiterate:
        if 'text' in displayformat:
            percents[card] = ' '*(maxcardlength - len(card)) + card
        if 'html' in displayformat:
            percents[card] = '<tr><td align=right>'+card+'</td>'
        if 'reddit' in displayformat:
            percents[card] = card

        for i in range(displaymaxturns):

            # If we are using a draw dictionary, then we find the number of draws with drawsdictionary[card].
            # If we have a draws list, then it is a list of dictionaries, where for example on turn 4 we use draws[3][card]
            if displaydrawslist is not None:
                if card not in displaydrawslist[i]:
                    continue
                numberofdraws = displaydrawslist[i][card]
            else:
                if card not in displaydrawsdictionary:
                    continue
                numberofdraws = displaydrawsdictionary[card]

            if numberofdraws > 0:
                percent = displaycasts[i][card]/numberofdraws

                if 'text' in displayformat:
                    percents[card] += ('  Cast by '+str(i+1)+': '+'{:>6.1%}'.format(percent)+'')
                if 'html' in displayformat:
                    percents[card] += ('<td align=center>' + '{:.1%}'.format(percent))
                if 'reddit' in displayformat:
                    percents[card] += (' | ' + '{:.1%}'.format(percent))

                # This basic margin of error calculation is only valid if we have more than 30 trials and at least 5 successes and at least 5 failures.
                error = 1.96 * \
                    math.sqrt(displaycasts[i][card]*(numberofdraws -
                                                     displaycasts[i][card])/math.pow(numberofdraws, 3))

                if displaycasts[i][card] >= 5 and (numberofdraws-displaycasts[i][card]) >= 5 and numberofdraws >= 30 and error >= 0.0005:
                    # Only actually display the margin of error if it is at least 0.1% and if the statistics tells us this is even meaningful.
                    if 'text' in displayformat:
                        percents[card] += ('+-' + '{:<6.1%}'.format(error))
                    if 'html' in displayformat:
                        percents[card] += ('&plusmn;' + '{:.1%}'.format(error) + '</td>')
                    if 'reddit' in displayformat:
                        percents[card] += ('±' + '{:.1%}'.format(error))

                elif error < 0.0005:
                    # If we have the error down below 0.1%, display no error, since it is correct up to the number of significant digits displayed.
                    if 'text' in displayformat:
                        percents[card] += '        '
                else:
                    # If the problem is a small sample size, go with plus or minus question mark.
                    if 'text' in displayformat:
                        percents[card] += '+-???%  '
                    if 'html' in displayformat:
                        percents[card] += ('&plusmn;' + '???%')
                    if 'reddit' in displayformat:
                        percents[card] += ('±???%')

        if 'html' in displayformat:
            percents[card] += '</tr>'

    if 'html' in displayformat:
        percents[card] += '</table><hr>'

    if 'print' in displayformat:
        print(header)
        for card in sorted_cardstoiterate:
            print(percents[card])

    if 'file' in displayformat:
        if 'html' in displayformat:
            htmlfile = 'html/'+deckfile[:-4]+'.html'
            with open(htmlfile, 'w') as f:
                f.write('<html><head>Results for '+deckfile)
                f.write(header)
                for card in sorted_cardstoiterate:
                    f.write(percents[card])
                f.write('</html>')
            print('HTML successfully output to', htmlfile)
            print('')

        else:
            print('Non-html files not implemented.')


def compareDecks(list_of_deckfiles):
    """Given a list of deckfiles, we go look at which spells are in multiple of the list, so we can compare how they do."""

    # The plan is to make a list of all the spells; if they appear in more than one deck, then we will show them.
    # So, if decks_featuring[spell] contains multiple deckfiles, we can display that spell.
    decks_featuring = {}

    # We want to keep track of all the draws, casts, and maxturns so we don't have to repeatedly look them up.
    parseddraws = {}
    parsedcasts = {}
    parsedmaxturns = {}

    for deckfile in list_of_deckfiles:
        parseddraws[deckfile], parsedcasts[deckfile], parsedmaxturns[deckfile] = parseResults(
            'results/'+deckfile[:-4]+'-results.txt')
        for spell in parseddraws[deckfile][0]:
            if spell in decks_featuring:
                decks_featuring[spell].append(deckfile)
            else:
                decks_featuring[spell] = [deckfile]

    # Now remove all the spells that only appear once.
    marked_for_deletion = []
    for spell in decks_featuring:
        if len(decks_featuring[spell]) <= 1:
            marked_for_deletion.append(spell)
    for spell in marked_for_deletion:
        del decks_featuring[spell]

    # Sort all the spells by convertedManaCost, then alphabetically.
    spellstoiterate = list(decks_featuring.keys())
    sorted_spellstoiterate = []
    list_of_convertedManaCosts = list(
        set([cardDatabase[spell]['convertedManaCost'] for spell in spellstoiterate]))
    list_of_convertedManaCosts.sort()
    for convertedManaCost in list_of_convertedManaCosts:
        list_of_spells = [spell for spell in spellstoiterate if cardDatabase[spell]
                          ['convertedManaCost'] == convertedManaCost]
        list_of_spells.sort()
        sorted_spellstoiterate.extend(list_of_spells)

    # The header will be the decks we looked at. We'll just do this in reddit markdown.
    header = 'Spell'
    for deckfile in list_of_deckfiles:
        header += ' | '+deckfile
    header += '\n----'
    for deckfile in list_of_deckfiles:
        header += '|----'

    # Go through the spells in the right order, and see if any of them are cast "before curve."
    spells_before_curve = []
    for spell in sorted_spellstoiterate:
        convertedManaCost = cardDatabase[spell]['convertedManaCost']
        for deckfile in list_of_deckfiles:
            if len(parsedcasts[deckfile]) >= convertedManaCost - 1 and convertedManaCost >= 2:
                if spell in parsedcasts[deckfile][convertedManaCost - 2]:
                    if parsedcasts[deckfile][convertedManaCost - 2][spell] != 0:
                        if spell not in spells_before_curve:
                            spells_before_curve.append(spell)

    # Make a table for the spells cast before curve.
    if len(spells_before_curve) != 0:
        print('')
        print('The following percentages are for casts **ahead of curve**, i.e. cast the turn before their convertedManaCost.')
        print('')
        print(header)
        for spell in spells_before_curve:
            convertedManaCost = cardDatabase[spell]['convertedManaCost']
            spellline = spell
            for deckfile in list_of_deckfiles:
                spellline += ' | '
                if len(parsedcasts[deckfile]) >= convertedManaCost - 1:
                    if spell in parsedcasts[deckfile][convertedManaCost - 2]:
                        if parseddraws[deckfile][convertedManaCost - 2][spell] > 0:
                            casts = parsedcasts[deckfile][convertedManaCost - 2][spell]
                            draws = parseddraws[deckfile][convertedManaCost - 2][spell]
                            percent, error = proportion_confidence_interval(casts, draws)
                            spellline += '{:>6.1%}'.format(percent) + '±' + '{:.1%}'.format(error)
            print(spellline)

    # Then make a table for the spells on curve.
    print('')
    print('The following percentages are for casts **on curve**, i.e. cast the turn of their convertedManaCost.')
    print('')
    print(header)
    for spell in sorted_spellstoiterate:
        convertedManaCost = cardDatabase[spell]['convertedManaCost']
        spellline = spell
        for deckfile in list_of_deckfiles:
            spellline += ' | '
            if len(parsedcasts[deckfile]) >= convertedManaCost:
                if spell in parsedcasts[deckfile][convertedManaCost - 1]:
                    if parseddraws[deckfile][convertedManaCost - 1][spell] > 0:
                        casts = parsedcasts[deckfile][convertedManaCost - 1][spell]
                        draws = parseddraws[deckfile][convertedManaCost - 1][spell]
                        percent, error = proportion_confidence_interval(casts, draws)
                        spellline += '{:>6.1%}'.format(percent) + '±' + '{:.1%}'.format(error)
        print(spellline)

    print('')


def proportion_confidence_interval(casts, draws):
    """Does the intro statistics 95% confidence interval for a proportion."""
    if draws != 0:
        percent = casts / draws
        error = 1.96*math.sqrt(casts*(draws-casts)/math.pow(draws, 3))
        return percent, error
    else:
        return 0, 0


# TODO: Even better debugging output.
slowMode = False

debug = {}
debug['EachTrial'] = False
debug['parseMana'] = False
debug['parseDecklist'] = False
debug['checkManaAvailability'] = False
debug['storeResults'] = False

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # temp -- If you want to run a unit test in slow mode, paste it here.
    #slowMode = True
    #slowModeWait = ''
    # playHand(LineOfPlay([],['Plains','Forest','Satyr Wayfinder','Chained to the Rocks'],['Plains','Plains','Plains','Island','Mountain','Plains','Plains','Plains']),
#                                  ManaBase({'Plains': 7, 'Island': 1, 'Forest': 1, 'Mountain': 1, 'Satyr Wayfinder': 1, 'Chained to the Rocks': 1}),
#                                  3,       # maxturns here
#                                  False
#                                 )
    while True:
        decksToRun, maxturns, trials, onthedraw, mulligans = userInterface()
        runTrials(decksToRun, maxturns, trials, onthedraw, mulligans)
        print('')
