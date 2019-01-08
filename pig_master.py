import random
import numpy as np
import pickle
import fs
from tqdm import tqdm_notebook
import matplotlib.pyplot as plt


class PigPlayer:

    def __init__(self, name='peppa', write_to='',
                 strategy='random', hold_at=20, hold_p=0.2, learn_from=[]):
        # check input
        if not isinstance(name, str) or name == '':
            print("<name> has to be a non-empty string.")
            raise TypeError
        if not isinstance(write_to, str):
            print("<write_to> has to be a string.")
            raise TypeError
        if strategy not in ['random', 'hold', 'learn']:
            print("<strategy> has to be 'random', 'hold', or 'learn'.")
            raise TypeError
        if not isinstance(hold_at, int) or hold_at < 1 or hold_at >= 100:
            print("<hold_at> has to be an integer between 1 and 100.")
            raise TypeError
        if not isinstance(hold_p, (float, int)) or hold_p < 0 or hold_p > 1:
            print("<hold_p> has to be a float between 0 and 1.")
            raise TypeError
        if (strategy == 'learn' and
            not all([isinstance(learn_from, list), learn_from,
                     all(isinstance(source, str) for source in learn_from)])):
            print("<learn_from> has to be a non-empty list of strings.")
            raise ValueError
        # assign attributes to the PigPlayer
        self.name = name
        self.write_to = write_to
        self.strategy = strategy
        self.hold_at = hold_at
        self.hold_p = float(hold_p)
        self.learn_from = learn_from
        self.dec_matrix = None

    def __str__(self):
        # print general player information
        ret_str = ('Player: ' + self.name + '\nData written to: '
                   + self.write_to)
        # print strategy-specific information
        if self.strategy == 'random':
            ret_str = (ret_str + '\nStrategy: Random with probability '
                       + str(self.hold_p) + '.')
        if self.strategy == 'hold':
            ret_str = (ret_str + '\nStrategy: Hold at '
                       + str(self.hold_at) + '.')
        if self.strategy == 'learn':
            ret_str = (ret_str
                       + '\nStrategy: Learn from the following sources.\n')
            for s in self.learn_from:
                ret_str = ret_str + ' ' + s
        return ret_str

    def play_turn(self, own_score, opp_score, output=False):
        # intialise score counter and list of decisions for the turn
        turn_total = int(0)
        dec = []
        # loop until player rolls 1, decides to hold, or reaches 100
        while True:
            # roll die
            roll = random.randint(1, 6)
            if output:
                print('Turn: ' + str(turn_total))
                print('Roll: ' + str(roll))
            if roll == 1:
                if output:
                    print('Kicked out.')
                return [own_score, dec]
            # update turn_total and decide whether to continue or to hold
            turn_total = turn_total + roll
            decided_to_hold = self.decide(own_score, opp_score, turn_total)
            # if 100 already reached, decide() will still be called (above)
            # but it will always return True; in this case, the decision is
            # not recorded (below)
            if max(own_score, opp_score, turn_total) < 100:
                dec.append(
                    [own_score, opp_score, turn_total, int(decided_to_hold)])
            if decided_to_hold:
                if output:
                    print('Decided to hold.')
                break
        return [own_score + turn_total, dec]

    def decide(self, own_score, opp_score, turn_total):
        # if 100 has been reached, always hold
        if own_score + turn_total >= 100:
            return True
        strategy = self.strategy
        # a learner decides according to frequencies in the decision matrix
        if strategy == 'learn':
            m = self.dec_matrix[own_score, opp_score, turn_total]
            win_prob_when_hold = m[1, 1]/(m[1, 0] + m[1, 1])
            win_prob_when_cont = m[0, 1]/(m[0, 0] + m[0, 1])
            return (win_prob_when_hold > win_prob_when_cont)
        # holder always holds once threshold hold_at is reached
        if strategy == 'hold':
            return (turn_total >= self.hold_at)
        # otherwise decide randomly according to given probability
        if strategy == 'random':
            return (random.random() <= self.hold_p)

    def reload_decision_matrix(self, virt_fs):
        if self.strategy == 'learn' and virt_fs is not None:
            # if player is a learner, generate matrix of ones and add the
            # frequencies from the sources given by the 'learn_from' list
            source_counter = int(0)
            mat = np.ones((100, 100, 100, 2, 2), dtype=int)
            for s in self.learn_from:
                fname = s + '.p'
                if virt_fs.isfile(fname):
                    source_counter = source_counter + 1
                    mat_file = virt_fs.open(fname, 'rb')
                    mat = mat + pickle.load(mat_file)
                    mat_file.close()
            self.dec_matrix = (mat - source_counter
                               * np.ones((100, 100, 100, 2, 2), dtype=int))

    def record_decisions(self, virt_fs, decisions=[], has_won=True):
        if not self.write_to == '' and virt_fs is not None:
            fname = self.write_to + '.p'
            if virt_fs.isfile(fname):
                # if file exists, open it
                mat_file = virt_fs.open(fname, 'rb')
                mat = pickle.load(mat_file)
                mat_file.close()
            else:
                # otherwise, generate matrix of ones
                # (which gives a 50-50 to start with)
                mat = np.ones((100, 100, 100, 2, 2), dtype=int)
            for d in decisions:
                # then increase entries corresponding to the decisions
                # that were made
                temp = mat[d[0], d[1], d[2], d[3], int(has_won)]
                mat[d[0], d[1], d[2], d[3], int(has_won)] = temp + 1
            mat_file = virt_fs.open(fname, 'wb')
            pickle.dump(mat, mat_file)
            mat_file.close()

    def get_approx_experience(self):
        # a very rough estimate of the number of games learned from
        return sum(sum(self.dec_matrix[0, 0, 2]))*5


class PigTournament:

    def __init__(self, player1, player2):
        if not isinstance(player1, PigPlayer):
            print("<player1> has to be a PigPlayer.")
        if not isinstance(player2, PigPlayer):
            print("<player2> has to be a PigPlayer.")
        self.p1 = player1
        self.p2 = player2
        self.results = []

    def __str__(self):
        num_games = len(self.results)
        if num_games < 100:
            p1_wins = sum(self.results)
            ret_str = (self.p1.name + ' (' + str(p1_wins) + ' wins) : ('
                       + str(num_games - p1_wins) + ' wins) ' + self.p2.name)
        else:
            p1_wins = sum(self.results[-100:])
            ret_str = (self.p1.name + ' (' + str(p1_wins) + ' wins) : ('
                       + str(100 - p1_wins) + ' wins) ' + self.p2.name)
        return ret_str

    def play_game(self, virt_fs=None, output=True):
        # initialise player scores, list of decisions; reload decision matrix
        p1_score = int(0)
        p2_score = int(0)
        p1_decisions = []
        p2_decisions = []
        self.p1.reload_decision_matrix(virt_fs)
        self.p2.reload_decision_matrix(virt_fs)
        if output:
            print(str(p1_score) + ' : ' + str(p2_score))
        # flip coin to see whether player 2 starts
        if random.random() <= 0.5:
            # let player 2 play a turn, returns new score and
            # list of decisions
            temp = self.p2.play_turn(p2_score, p1_score, output)
            p2_score = temp[0]
            p2_decisions = p2_decisions + temp[1]
            if output:
                print(str(p1_score) + ' : ' + str(p2_score))
        while max(p1_score, p2_score) < 100:
            temp = self.p1.play_turn(p1_score, p2_score, output)
            p1_score = temp[0]
            p1_decisions = p1_decisions + temp[1]
            if output:
                print(str(p1_score) + ' : ' + str(p2_score))
            temp = self.p2.play_turn(p2_score, p1_score, output)
            p2_score = temp[0]
            p2_decisions = p2_decisions + temp[1]
            if output:
                print(str(p1_score) + ' : ' + str(p2_score))
        p1_won = (p1_score >= 100)
        self.results = self.results + [p1_won]
        if p1_won:
            # record p1's decisions as winning decisions ...
            self.p1.record_decisions(virt_fs, p1_decisions, True)
            # ... and p2's decisions as losing decisions
            self.p2.record_decisions(virt_fs, p2_decisions, False)
        else:
            self.p1.record_decisions(virt_fs, p1_decisions, False)
            self.p2.record_decisions(virt_fs, p2_decisions, True)
        return [p1_won]

    def play_games(self, n=100, output=False):
        # open real and virtual file system
        real_fs = fs.open_fs('./player_data/')
        virt_fs = fs.open_fs('mem://')
        # copy data from the real file system to the virtual one,
        # work in the virtual file system in the following
        fs.copy.copy_fs(real_fs, virt_fs)
        for k in tqdm_notebook(range(n)):
            self.play_game(virt_fs, output)
        # update the real file system and close both files systems
        fs.copy.copy_fs(virt_fs, real_fs)
        real_fs.close()
        virt_fs.close()

    def results_as_sequence(self, n=100):
        m = (len(self.results) // n) * n
        temp = np.asarray(self.results[:m]).astype(int).reshape((-1, n))
        return list(np.sum(temp, axis=1))

    def plot_results(self, n=100):
        li = self.results_as_sequence(n)
        plt.plot(li)

    def reset_results(self):
        self.results = []
