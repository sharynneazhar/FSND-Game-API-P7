# FSND-Game-API-P7
Nanodegree Project: Backend API Service for the game of War

### Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
running by visiting the API Explorer - by default `localhost:8080/_ah/api/explorer`.
3.  (Optional) Generate your client library(ies) with the endpoints tool.
Deploy your application.

### Game Description:
War is a card game typically involving two players. It uses a standard playing card deck. However, the app will only use 26 cards to keep the game short.

The objective of the game is to win all the cards.

The deck is divided evenly among the two players. In unison, each player reveals the top card of their deck – this is a "battle" – and the player with the higher card takes both of the cards played and adds them to their deck. Aces are high, and suits are ignored.

If the two cards played are of equal value, then there is a "war". Both players place the next card from their deck face down in a pool and battle with the next top card of their deck. The higher face-up card wins the war and adds all six cards to the bottom of their deck. If the face-up cards are again equal then the battle repeats with another set of cards. This repeats until one player's face-up card is higher than their opponent's. A player will lose if their deck is empty or runs out of cards during a war.

### Files Included:
- api.py: Contains endpoints and game playing logic.
- app.yaml: App configuration.
- cron.yaml: Cronjob configuration.
- main.py: Handler for taskqueue handler.
- models.py: Entity definitions including helper methods.
- forms.py: Message form definitions.
- utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

### Endpoints Included:
**create_user**
- Path: 'user'
- Method: POST
- Parameters: user_name, email (optional)
- Returns: Message confirming creation of the User.
- Description: Creates a new User. user_name provided must be unique. Will
raise a ConflictException if a User with that user_name already exists.

**get_user_games**
- Path: 'user/active_games',
- Method: GET
- Parameters: user_name
- Returns: A list of game IDs with active status
- Description: Returns the username and all game IDs where game_over is False; a message will be returned if there are no active games found

**new_game**
- Path: 'game'
- Method: POST
- Parameters: user_name
- Returns: GameForm with initial game state.
- Description: Creates a new Game. user_name provided must correspond to an
existing user - will raise a NotFoundException if not.

**get_game**
- Path: 'game/{urlsafe_game_key}'
- Method: GET
- Parameters: urlsafe_game_key
- Returns: GameForm with current game state.
- Description: Returns the current state of a game.

**cancel_game**
- Path: 'game/{urlsafe_game_key}/cancel'
- Method: PUT
- Parameters: urlsafe_game_key
- Returns: Message confirming game cancellation.
- Description: Accepts the game key and deletes the entity from the datastore. Returns a NotFoundException if a Game with the game key does not exist

**get_game_history**
- Path: 'game/{urlsafe_game_key}/history'
- Method: GET
- Parameters: urlsafe_game_key
- Returns: A list of GameRound objects.
- Description: Returns a list of GameRound objects containing information about the cards played and the winner of the round

**battle**
- Path: 'game/{urlsafe_game_key}/battle'
- Method: PUT
- Parameters: urlsafe_game_key
- Returns: GameForm with new game state.
- Description: Simulates the card battle and returns the updated state of the game. A record of moves will be recorded at the each of each round. If the User wins the game, a corresponding User win record will be incremented.

**get_user_rankings**
- Path: 'rankings'
- Method: GET
- Parameters: none
- Returns: UserRanking
- Description: Returns all Users sorted by number of wins.

## Models Included:
- **User** - Stores unique user_name, (optional) email address, and number of wins.
- **Game** - Stores unique game states. Associated with User model via KeyProperty.

## Response Forms Included:
- **GenericForm** - General purpose response representations
- **GameForm** - Representation of a Game's state
- **UserGameForm** - Representation of a User's list of active games
- **UserStatsForm** - Representation of a User's win records
- **UserRankingForm** - Representation of user rankings by wins
- **GameRoundForm** - Representation of a battle round
- **GameHistoryForm** - Representation of a Game's history of plays
