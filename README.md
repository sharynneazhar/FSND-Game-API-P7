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

The deck is divided evenly among the two players, giving each a down stack. In unison, each player reveals the top card of their deck – this is a "battle" – and the player with the higher card takes both of the cards played and adds them to their deck. Aces are high, and suits are ignored.

If the two cards played are of equal value, then there is a "war". Both players place the next card from their deck face down and battle with the next top card. The higher face-up card wins the war and adds all six cards to the bottom of their deck. If the face-up cards are again equal then the battle repeats with another set of face-down/up cards. This repeats until one player's face-up card is higher than their opponent's. A player will lose if their deck is empty or runs out of cards during a war.

### Files Included:
- api.py: Contains endpoints and game playing logic.
- app.yaml: App configuration.
- cron.yaml: Cronjob configuration.
- main.py: Handler for taskqueue handler.
- models.py: Entity and message definitions including helper methods.
- utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

### Endpoints Included:
**create_user**
- Path: 'user'
- Method: POST
- Parameters: user_name, email (optional)
- Returns: Message confirming creation of the User.
- Description: Creates a new User. user_name provided must be unique. Will
raise a ConflictException if a User with that user_name already exists.

**new_game**
- Path: 'game'
- Method: POST
- Parameters: user_name, min, max, attempts
- Returns: GameForm with initial game state.
- Description: Creates a new Game. user_name provided must correspond to an
existing user - will raise a NotFoundException if not. Min must be less than
max. Also adds a task to a task queue to update the average moves remaining
for active games.

**get_game**
- Path: 'game/{urlsafe_game_key}'
- Method: GET
- Parameters: urlsafe_game_key
- Returns: GameForm with current game state.
- Description: Returns the current state of a game.

**make_move**
- Path: 'game/{urlsafe_game_key}'
- Method: PUT
- Parameters: urlsafe_game_key, guess
- Returns: GameForm with new game state.
- Description: Accepts a 'guess' and returns the updated state of the game.
If this causes a game to end, a corresponding Score entity will be created.

**get_scores**
- Path: 'scores'
- Method: GET
- Parameters: None
- Returns: ScoreForms.
- Description: Returns all Scores in the database (unordered).

**get_user_scores**
- Path: 'scores/user/{user_name}'
- Method: GET
- Parameters: user_name
- Returns: ScoreForms.
- Description: Returns all Scores recorded by the provided player (unordered).
Will raise a NotFoundException if the User does not exist.

**get_active_game_count**
- Path: 'games/active'
- Method: GET
- Parameters: None
- Returns: StringMessage
- Description: Gets the average number of attempts remaining for all games
from a previously cached memcache key.

## Models Included:
- **User** - Stores unique user_name and (optional) email address.
- **Game** - Stores unique game states. Associated with User model via KeyProperty.

## Response Forms Included:
- **GameResponse** - Representation of a Game's state
- **UserGameResponse** - Representation of a User's list of games
- **UserStats** - Representation of a User's win records
- **UserRankingResponse** - Representation of user rankings by wins
- **GenericMessage** - General purpose response representations
