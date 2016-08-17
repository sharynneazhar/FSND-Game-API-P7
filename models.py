"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    user_deck = ndb.StringProperty(repeated=True)
    bot_deck = ndb.StringProperty(repeated=True)
    game_over = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        # Generate card deck and shuffle
        deck = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'] * 2
        random.shuffle(deck)
        deck1 = deck[0:13]
        deck2 = deck[13:26]

        game = Game(user=user,
                    user_deck=deck1,
                    bot_deck=deck2,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns the response data of the game object"""
        form = GameResource()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.user_deck = self.user_deck
        form.bot_deck = self.bot_deck
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game -- if won is True, the player won;
        if won is False, the player lost"""
        self.game_over = True
        self.put()


class GenericMessage(messages.Message):
    """Generic string message"""
    message = messages.StringField(1, required=True)


class GameResource(messages.Message):
    """Returns game information"""
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    user_deck = messages.StringField(3, repeated=True)
    bot_deck = messages.StringField(4, repeated=True)
    message = messages.StringField(5, required=True)
    game_over = messages.BooleanField(6, required=True)


class GamesByUserResource(messages.Message):
    """Returns a list of games in play"""
    user_name = messages.StringField(1, required=True)
    games = messages.StringField(2, repeated=True)
