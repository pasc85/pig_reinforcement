class PigPlayer:

    def __init__(self, name='peppa', write_to='',
                 strategy='random', hold_at=20, hold_p=0.2, learn_from=[],
                 print_player_info=True):
        # check input
        if not isinstance(name, str) or name == '':
            print("<name> has to be a non-empty string.")
            raise ValueError
        if not isinstance(write_to, str):
            print("<write_to> has to be a string.")
            raise TypeError
        if strategy not in ['random', 'hold', 'learn']:
            print("<strategy> has to be 'random', 'hold', or 'learn'.")
            raise ValueError
        if not isinstance(hold_at, int) or hold_at < 1 or hold_at > 100:
            print("<hold_at> has to be an integer between 1 and 100.")
            raise ValueError
        if not isinstance(hold_p, (float, int)) or hold_p < 0 or hold_p > 1:
            print("<hold_p> has to be a float between 0 and 1.")
            raise ValueError
        if (not isinstance(learn_from, list)
                or not all(isinstance(source, str) for source in learn_from)):
            print("<learn_from> has to be a list of strings.")
            raise ValueError
        if not isinstance(print_player_info, bool):
            print("<print_player_info> has to be boolean.")
            raise TypeError
        # assign attributes to the PigPlayer
        self.name = name
        self.write_to = write_to
        self.strategy = strategy
        self.hold_at = hold_at
        self.hold_p = float(hold_p)
        self.learn_from = learn_from
        # print summary of player information
        if print_player_info:
            print('Player: ' + self.name)
            print('Data written to: ' + self.write_to)
            if strategy == 'random':
                print('Strategy: Random with probability ' + str(self.hold_p))
            if strategy == 'hold':
                print('Strategy: Hold at ' + str(self.hold_at))
            if strategy == 'hold':
                print('Strategy: Learn from the ' + str(len(self.learn_from))
                      + ' given sources.')
