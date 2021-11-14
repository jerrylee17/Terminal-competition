import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from queue import PriorityQueue

from gamelib.game_state import GameState
from gamelib.navigation import ShortestPathFinder


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
        gamelib.debug_write("Random seed: {}".format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
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
        self.GAME_ROUND = 1
        self.upgrade_priority = []
        self.nonessential_structures = []
        
        # This is a good place to do initial setup

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)

        self.build_structures(game_state)

        # Attack stage
        self.attack_edge(game_state)

        game_state.submit_turn()

    def build_structures(self, game_state: GameState):
        
        essential_structures = [
            (TURRET, [3, 12]), 
            (TURRET, [24, 12]), 
            (TURRET, [9, 10]), 
            (TURRET, [18, 10]), 
            (TURRET, [13, 10]),
            (WALL, [1, 13]),
            (WALL, [2, 13]),
            (WALL, [3, 13]), 
            (WALL, [4, 13]),
            (WALL, [23, 13]),
            (WALL, [5, 13]),
            (WALL, [22, 13]),
            (WALL, [24, 13]),
            (WALL, [25, 13]),
            (WALL, [26, 13]),
            (WALL, [27, 13]),
            (WALL, [8, 11]),
            (WALL, [9, 11]),
            (WALL, [10, 11]),
            (WALL, [17, 11]),
            (WALL, [18, 11]),
            (WALL, [19, 11]),
            (WALL, [0, 13]),
            (WALL, [12, 11]),
            (WALL, [13, 11]),
            (WALL, [14, 11])
        ]
        #structures = [(i, k) for i, k in enumerate(structures)]
        nonessentials = [
            (TURRET, [21, 11]),
            (TURRET, [6, 11]),
            (WALL, [21, 11]),
            (SUPPORT, [8, 10]),
            (SUPPORT, [19, 10]),
            (SUPPORT, [23, 11]),
            (WALL, [7, 11]),
            (WALL, [21, 12]),
            (WALL, [6, 12]),
            (WALL, [5, 12]),
            (SUPPORT, [4, 11]),
            (WALL, [20, 12])
        ]
        # helper
        def near_turret(loc):
            if game_state.contains_stationary_unit(loc).unit_type == "TURRET":
                return True
            elif game_state.contains_stationary_unit([loc[0], loc[1]-1]) == "TURRET":
                return True
            elif game_state.contains_stationary_unit([loc[0]-1, loc[1]-1]) == "TURRET":
                return True
            elif game_state.contains_stationary_unit([loc[0]+1, loc[1]-1]) == "TURRET":
                return True
            return False
            
        # add initial structures, respawn if structure was destroyed
        while (game_state.get_resource(0) >= 5) and essential_structures:
            struc_type, loc = essential_structures.pop(0)
            curr_structure = game_state.contains_stationary_unit(loc)
            if game_state.can_spawn(struc_type, loc):
                game_state.attempt_spawn(struc_type, loc)
                # add to upgrade queue
                # if self.GAME_ROUND > 1:
                if(near_turret):
                    self.upgrade_priority = [(struc_type, loc)] + self.upgrade_priority
                        # nonessentials = [(TURRET, (loc[0]+1, loc[1]))] + nonessentials
            elif curr_structure:
                if curr_structure.health < curr_structure.max_health/2:
                    if struc_type == TURRET:
                        if loc[0] < 13:
                            self.nonessential_structures.append((TURRET, (loc[0]+1, loc[1])))
                        else:
                            self.nonessential_structures.append((TURRET, (loc[0]-1, loc[1])))
                            
        # upgrade 
        while (game_state.get_resource(0) >= 7) and self.upgrade_priority:
            struc_type, loc = self.upgrade_priority.pop(0)
            game_state.attempt_upgrade(loc)

        self.nonessential_structures = self.nonessential_structures + nonessentials
        while (game_state.get_resource(0) >= 5) and self.nonessential_structures:
            structure = self.nonessential_structures.pop(0)
            gamelib.debug_write(structure)
            struc_type, loc = structure
            if game_state.can_spawn(struc_type, loc):
                game_state.attempt_spawn(struc_type, loc)
            if(struc_type == TURRET):
                self.upgrade_priority = [(struc_type, loc)] + self.upgrade_priority

        self.GAME_ROUND += 1
        
        # Attack stage
        self.attack_edge(game_state)


    def calc_left_resistance(self, game_state: GameState):
        left_edges = [
            [0, 13],
            [1, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [5, 8],
            [6, 7],
            [7, 6],
            [8, 5],
            [9, 4],
            [10, 3],
            [11, 2],
            [12, 1],
            [13, 0],
        ]
        left_destinations = [
            [14, 27],
            [15, 26],
            [16, 25],
            [17, 24],
            [18, 23],
            [19, 22],
            [20, 21],
            [21, 20],
            [22, 19],
            [23, 18],
            [24, 17],
            [25, 16],
            [26, 15],
            [27, 14],
            [13, 0],
            [14, 0],
        ]

        edge_resistance = {}
        pathfinder = ShortestPathFinder()
        for pos in left_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, left_destinations, game_state
            )
            if path_edges is None:
                continue
            for path in path_edges:
                # Still on my territory
                if path[1] < 11:
                    continue
                # Add number of attackers
                edge_resistance[pos] = edge_resistance.get(pos, 0) + len(
                    game_state.get_attackers(path, 0)
                )
        return edge_resistance

    def calc_right_resistance(self, game_state: GameState):
        right_edges = [
            [27, 13],
            [26, 12],
            [25, 11],
            [24, 10],
            [23, 9],
            [22, 8],
            [21, 7],
            [20, 6],
            [19, 5],
            [18, 4],
            [17, 3],
            [16, 2],
            [15, 1],
            [14, 0],
        ]
        right_destinations = [
            [13, 27],
            [12, 26],
            [11, 25],
            [10, 24],
            [9, 23],
            [8, 22],
            [7, 21],
            [6, 20],
            [5, 19],
            [4, 18],
            [3, 17],
            [2, 16],
            [1, 15],
            [0, 14],
        ]

        edge_resistance = {}
        pathfinder = ShortestPathFinder()
        for pos in right_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, right_destinations, game_state
            )
            if path_edges is None:
                continue
            for path in path_edges:
                # Still on my territory
                if path[1] < 11:
                    continue
                # Add number of attackers and register edge
                edge_resistance[pos] = edge_resistance.get(pos, 0) + len(
                    game_state.get_attackers(path, 0)
                )
        return edge_resistance

    def attack_edge(self, game_state: GameState):
        if game_state.get_resource(1) < 11:
            gamelib.debug_write(
                f"Insufficient units to attack: {game_state.get_resource(1)}"
            )
            return

        # Determine resistance on left
        left_resistance = self.calc_left_resistance(game_state)
        lowest_left_resistance = min(left_resistance.values())
        filtered_left_resistance = [
            k for k, v in left_resistance.items() if v == lowest_left_resistance
        ]

        # Determine resistance on right
        right_resistance = self.calc_right_resistance(game_state)
        lowest_right_resistance = min(right_resistance.values())
        filtered_right_resistance = [
            k for k, v in right_resistance.items() if v == lowest_right_resistance
        ]

        def attack_left():
            for left in filtered_left_resistance:
                left = list(left)
                if game_state.can_spawn(SCOUT, left):
                    gamelib.debug_write(
                        f"Attacking on {left} with {game_state.get_resource(1)}"
                    )
                    game_state.attempt_spawn(
                        SCOUT, list(left), num=int(game_state.get_resource(1))
                    )
                    return True
            return False

        def attack_right():
            for right in filtered_right_resistance:
                right = list(right)
                if game_state.can_spawn(SCOUT, right):
                    gamelib.debug_write(
                        f"Attacking on {right} with {game_state.get_resource(1)}"
                    )
                    game_state.attempt_spawn(
                        SCOUT, list(right), num=int(game_state.get_resource(1))
                    )
                    return True
            return False

        # Attack left
        if lowest_left_resistance < lowest_right_resistance:
            if not attack_left():
                # If attack left fails, attack right
                attack_right()
        else:
            # Attack right
            if not attack_right():
                # If attack right fails, attack left
                attack_left()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
