"""forms.py - """

from protorpc import messages


class GenericForm(messages.Message):
    """Generic string message"""
    message = messages.StringField(1, required=True)


class GameForm(messages.Message):
    """Returns game information"""
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    user_card = messages.StringField(3)
    bot_card = messages.StringField(4)
    user_card_count = messages.IntegerField(5, default=0)
    bot_card_count = messages.IntegerField(6, default=0)
    message = messages.StringField(7, required=True)
    game_over = messages.BooleanField(8, required=True)


class UserGameForm(messages.Message):
    """Returns a list of games in play"""
    user_name = messages.StringField(1, required=True)
    activeGames = messages.StringField(2, repeated=True)
    message = messages.StringField(3)


class UserStatsForm(messages.Message):
    """Object to store a User's game stats"""
    user_name = messages.StringField(1)
    wins = messages.IntegerField(2)


class UserRankingForm(messages.Message):
    """Returns a list of users ordered by number of wins"""
    message = messages.StringField(1, required=True)
    rankings = messages.MessageField(UserStatsForm, 2, repeated=True)


class GameRoundForm(messages.Message):
    """Object to store information about a round"""
    user_card = messages.StringField(1, required=True)
    bot_card = messages.StringField(2, required=True)
    result = messages.StringField(3, required=True)


class GameHistoryForm(messages.Message):
    """Returns a history of rounds played"""
    user_name = messages.StringField(1, required=True)
    history = messages.MessageField(GameRoundForm, 2, repeated=True)
