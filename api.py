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

from utils import get_by_urlsafe

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

    def _getRank(self, cardValue):
        """Return the numeric value of a card -- important for face cards"""
        return { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14 }[cardValue]


    def _handleWarRound(self, user_card, bot_card, game, card_stack=[]):
        """War -- played when the cards have equal value."""
        if (len(game.user_deck) < 2):
            msg = 'The bot won the war... '
            game.end_game(False)
            return [game, msg]
        else:
            user_skip_card = game.user_deck.pop(0);
            user_war_card = game.user_deck.pop(0);
            user_war_card_value = self._getRank(user_war_card)

        if (len(game.bot_deck) < 2):
            msg = 'You win the war! '
            game.end_game(True)
            return [game, msg]
        else:
            bot_skip_card = game.bot_deck.pop(0);
            bot_war_card = game.bot_deck.pop(0);
            bot_war_card_value = self._getRank(bot_war_card)

        if (user_war_card_value > bot_war_card_value):
            msg = 'You win the war! '
            game.user_deck.extend([user_card, bot_card, user_skip_card,
                bot_skip_card, user_war_card, bot_war_card] + card_stack)
            return [game, msg]
        elif (user_war_card_value < bot_war_card_value):
            msg = 'The bot won the war... '
            game.bot_deck.extend([user_card, bot_card, user_skip_card,
                bot_skip_card, user_war_card, bot_war_card] + card_stack)
            return [game, msg]
        else:
            stack = [user_card, bot_card, user_skip_card,
                bot_skip_card, user_war_card, bot_war_card]
            results = self._handleWarRound(user_war_card, bot_war_card,
                game, stack)
            return results


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
                      response_message=GamesByUserResource,
                      path='user/getActiveGames',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of a user's active and inactive (done) games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('User does not exist!')

        games = Game.query(Game.user == user.key).fetch()
        activeGames = []
        inactiveGames = []
        for game in games:
            if (game.game_over == False):
                activeGames.append(game.key.id())
            else:
                inactiveGames.append(game.key.id())

        return GamesByUserResource(user_name=request.user_name,
                                   activeGameIds=activeGames,
                                   inactiveGameIds=inactiveGames)


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
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancels an active game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return GenericMessage(message="Game already completed")
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

        # Get the first card from each player's deck
        user_card = game.user_deck.pop(0)
        bot_card = game.bot_deck.pop(0)

        # Get the integer value of the card
        user_card_value = self._getRank(user_card)
        bot_card_value = self._getRank(bot_card)

        # Analyze battle
        if (user_card_value > bot_card_value):
            msg = 'You win this round! '
            game.user_deck.extend([user_card, bot_card])
        elif (user_card_value < bot_card_value):
            msg = 'The bot won this time... '
            game.bot_deck.extend([user_card, bot_card])
        else:
            results = self._handleWarRound(user_card, bot_card, game)
            user_deck = results[0].user_deck
            bot_deck = results[0].bot_deck
            msg = results[1]

        if not game.user_deck:
            game.end_game(False)
            return game.to_form('You lose. Game over!')
        elif not game.bot_deck:
            game.end_game(True)
            return game.to_form('You win. Game over!')
        else:
            game.put()
            return game.to_form(msg)

        

    ## TODO add ability to track user rankings by win/loss
    ## get_user_rankings

    ## TODO add ability to track a game history
    ## get_game_history

api = endpoints.api_server([WarApi])
