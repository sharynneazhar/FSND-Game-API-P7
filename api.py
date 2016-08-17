# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

import random
import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game

from models import GenericMessage
from models import GameResource
from models import GamesByUserResource

from utils import get_by_urlsafe, getRank

USER_REQUEST = endpoints.ResourceContainer(
    user_name = messages.StringField(1),
    email = messages.StringField(2))
NEW_GAME_REQUEST = endpoints.ResourceContainer(
    user_name = messages.StringField(1))
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key = messages.StringField(1))
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key = messages.StringField(1))
CURRENT_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name = messages.StringField(1))
BATTLE_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key = messages.StringField(1))


@endpoints.api(name='war', version='v1')
class WarApi(remote.Service):
    """War API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GenericMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException('User already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return GenericMessage(message='User {} created!'\
            .format(request.user_name))

    @endpoints.method(request_message=CURRENT_GAMES_REQUEST,
                      response_message=GenericMessage,
                      path='user/getActiveGames',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of a user's active games"""
        user = User.query(User.name == request.user_name).get()

        if not user:
            raise endpoints.NotFoundException('User does not exist!')

        game = Game.query(Game.user == user.key)
        return GenericMessage(message='get')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameResource,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Aw snap, the game is getting intense')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameResource,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('User does not exist!')

        try:
            game = Game.new_game(user.key)
        except ValueError:
            raise endpoints.BadRequestException('Error creating new game.')

        return game.to_form('Good luck playing the game of War!')

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=GenericMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancels (deletes from datastore) an active game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            game.key.delete()
            return GenericMessage(message='Game was canceled')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=BATTLE_REQUEST,
                      response_message=GameResource,
                      path='game/{urlsafe_game_key}/battle',
                      name='battle',
                      http_method='PUT')
    def battle(self, request):
        """Battle -- reveal top card from deck. Returns the game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return game.to_form('Game already over')

        user_card = game.user_deck.pop(0)
        bot_card = game.bot_deck.pop(0)
        result = 'Bot: ' + bot_card + '; You: ' + user_card + ' '

        if (getRank(user_card) > getRank(bot_card)):
            game.user_deck.extend([user_card, bot_card])
            msg = 'You win this round!'
        elif (getRank(user_card) < getRank(bot_card)):
            game.bot_deck.extend([user_card, bot_card])
            msg = 'The bot won this time...'
        else:
            ## TODO start war round
            msg = 'It\'s a tie!'

        if len(game.user_deck) == 52:
            game.end_game(True)
            return game.to_form(result + msg + ' Game over!')
        elif len(game.bot_deck) == 52:
            game.end_game(False)
            return game.to_form(result + msg + ' Game over!')
        else:
            game.put()
            return game.to_form(result + msg)




    ## TODO add war endpoint method

    ## TODO manage card stacks

    ## TODO add ability to track user rankings by win/loss
    ## get_user_rankings

    ## TODO add ability to track a game history
    ## get_game_history

api = endpoints.api_server([WarApi])
