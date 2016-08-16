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
        deck = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'] * 4
        random.shuffle(deck)
        deck1 = deck[0:26]
        deck2 = deck[26:52]

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


class GenericMessage(messages.Message):
    """GenericMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class UserResource(messages.Message):
    user_name = messages.StringField(1, required=True)
    email = messages.StringField(2)


class GameResource(messages.Message):
    """Game form for outbound api response data"""
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    user_deck = messages.StringField(3, repeated=True)
    bot_deck = messages.StringField(4, repeated=True)
    message = messages.StringField(5, required=True)
    game_over = messages.BooleanField(6, required=True)


class NewGameResource(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
