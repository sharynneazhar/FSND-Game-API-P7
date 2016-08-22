# -*- coding: utf-8 -*-`
"""api.py"""

import random
import logging
import endpoints

from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User
from models import Game

from forms import GenericForm
from forms import GameForm
from forms import UserGameForm
from forms import UserStatsForm
from forms import UserRankingForm
from forms import GameRoundForm
from forms import GameHistoryForm

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
ACTIVE_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name = messages.StringField(1))
BATTLE_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key = messages.StringField(1))


@endpoints.api(name='war', version='v1')
class WarApi(remote.Service):
    """War API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GenericForm,
                      path='user/new',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Creates a new User"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException('User already exists')
        User(name=request.user_name, email=request.email).put()
        return GenericForm(message='User {} created'.format(request.user_name))

    @endpoints.method(request_message=ACTIVE_GAMES_REQUEST,
                      response_message=UserGameForm,
                      path='user/active_games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns a list of active games by User"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('User does not exist!')

        games = Game.query(Game.user == user.key).fetch()
        activeGames = []
        for game in games:
            if (game.game_over == False):
                activeGames.append(game.key.id())
            else:
                return UserGameForm(user_name=request.user_name,
                                    message='User has no active games')
        return UserGameForm(user_name=request.user_name,
                            activeGameIds=activeGames)

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('User does not exist')

        try:
            game = Game.new_game(user.key)
        except ValueError:
            raise endpoints.BadRequestException('Error creating new game.')

        return game.to_form('Successfully created a new game!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Returns the current game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Successfully retrieved game')
        else:
            raise endpoints.NotFoundException('Game not found')


    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=GenericForm,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancels an active game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return GenericForm(message="Game already over")
            game.key.delete()
            return GenericForm(message='Game was canceled')
        else:
            raise endpoints.NotFoundException('Game not found')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns a record of plays made during a game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return GameHistoryForm(user_name=game.user.get().name,
                               history=game.history)


    def _getRank(self, card):
        """Returns the numeric representation of a given card"""
        return { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
            '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14 }[card]


    def _handleBattleRound(self,
                           game,
                           user_card='',
                           bot_card='',
                           war_card_pool=[]):
        """Handles the battle round"""
        if game.user_deck and game.bot_deck: # not empty
            # Get the first card from each player's deck
            user_card = game.user_deck.pop(0)
            bot_card = game.bot_deck.pop(0)

            # Get the integer value of the card
            user_card_value = self._getRank(user_card)
            bot_card_value = self._getRank(bot_card)

            if user_card_value > bot_card_value:
                result = 'Player won.'
                game.user_deck.extend([user_card, bot_card] + war_card_pool)
                war_card_pool  = []
            elif user_card_value < bot_card_value:
                result = 'Bot won.'
                game.bot_deck.extend([user_card, bot_card] + war_card_pool)
                war_card_pool  = []
            else: # equal card values
                result = 'It\'s a war.'

                # add the current cards to the winning pool
                war_card_pool.extend([user_card] + [bot_card])
                roundInfo = GameRoundForm(user_card=user_card,
                                          bot_card=bot_card,
                                          result=result)
                game.history.append(roundInfo)

                # in a war, players need to skip one card and battle again
                # with the next top card. If a player runs out of cards,
                # the game is over
                if game.user_deck:
                    war_card_pool.extend([game.user_deck.pop(0)])
                else:
                    result = 'Game over. Bot won it all in the war.'
                    game.bot_deck.extend(war_card_pool)
                    game.put()
                    game.end_game(False)

                if game.bot_deck:
                    war_card_pool.extend([game.bot_deck.pop(0)])
                else:
                    result = 'Game over. Player won it all in the war.'
                    game.user_deck.extend(war_card_pool)
                    game.put()
                    game.end_game(True)

                game.put()
                return self._handleBattleRound(game, war_card_pool=war_card_pool)

        if not game.user_deck:
            result = 'Game over. Bot won.'
            game.end_game(False)
        elif not game.bot_deck:
            result = 'Game over. Player won.'
            game.end_game(True)

        roundInfo = GameRoundForm(user_card=user_card,
                                  bot_card=bot_card,
                                  result=result)
        game.history.append(roundInfo)
        game.put()
        return result


    @endpoints.method(request_message=BATTLE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/battle',
                      name='battle',
                      http_method='PUT')
    def battle(self, request):
        """Returns the game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over.')
        result = self._handleBattleRound(game)
        return game.to_form(result)


    @endpoints.method(response_message=UserRankingForm,
                      path='rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns a user rankings ordered by number of wins."""
        users = User.query().order(-User.wins)
        rankings = []
        for user in users:
            stats = UserStatsForm(user_name=user.name, wins=user.wins)
            rankings.append(stats)
        return UserRankingForm(message='Success', rankings=rankings)


api = endpoints.api_server([WarApi])
