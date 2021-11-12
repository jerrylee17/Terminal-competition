import gamelib
import random
import math
import warnings
from sys import maxsize
import json

from gamelib.game_state import GameState


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(
            game_state.turn_number))
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)

        self.hello_world(game_state)

        game_state.submit_turn()

    def hello_world(self, game_state: GameState):
        turret_pos = [
            (3, 12),
            (24, 12),
            (10, 10),
            (17, 10)
        ]
        wall_pos_1 = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [5, 13], [
            22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13]]

        wall_pos_2 = [[8, 11], [9, 11], [10, 11], [11, 11], [
            12, 11], [15, 11], [16, 11], [17, 11], [18, 11], [19, 11]]

        for pos in turret_pos:
            if game_state.can_spawn(TURRET, pos):
                game_state.attempt_spawn(TURRET, pos)
            else:
                game_state.attempt_upgrade(pos)

        for pos in wall_pos_1:
            if game_state.can_spawn(WALL, pos):
                game_state.attempt_spawn(WALL, pos)
            else:
                game_state.attempt_upgrade(pos)

        for pos in wall_pos_2:
            if game_state.can_spawn(WALL, pos):
                game_state.attempt_spawn(WALL, pos)
            else:
                game_state.attempt_upgrade(pos)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
