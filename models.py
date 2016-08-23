"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from forms import GameForm
from forms import GameRoundForm


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(default=0)


class Game(ndb.Model):
    """Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    user_deck = ndb.StringProperty(repeated=True)
    bot_deck = ndb.StringProperty(repeated=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    history = msgprop.MessageProperty(GameRoundForm, repeated=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        # Generate card deck and shuffle - 26 cards to keep the game short
        deck = ['2', '3', '4', '5', '6', '7', '8', '9',
                '10', 'J', 'Q', 'K', 'A'] * 2
        # uncomment these lines to test war cases and to end the game faster
        # deck = ['2', '2', '2', '2', '2', '2', '2', '2',
        #         '2', '2', '2', 'K', 'A'] * 2
        random.shuffle(deck)
        deck1 = deck[0:13]
        deck2 = deck[13:26]
        game = Game(user=user, user_deck=deck1,
                    bot_deck=deck2)
        game.put()
        return game

    def to_form(self, result):
        """Returns the response data of the game object"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        if ('user_card' in result) and ('bot_card' in result):
            form.user_card = result['user_card']
            form.bot_card = result['bot_card']
        form.user_card_count = len(self.user_deck)
        form.bot_card_count = len(self.bot_deck)
        form.game_over = self.game_over
        form.message = result['message']
        return form

    def end_game(self, won=False):
        """Ends the game -- if won is True, the player won;
        if won is False, the player lost"""
        user = User.query(User.name == self.user.get().name).get()
        if won:
            user.wins += 1
            user.put()
        self.game_over = True
        self.put()
