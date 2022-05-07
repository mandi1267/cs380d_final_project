import numpy as np

class MultiArmedBanditExecutor:
    """
    Object that should take in results information and determine the value(s) of m to use for the next observation
    period.
    """

    def __init__(self, mOptions, multiArmedBanditConfig):
        """
        Initialize the multi-armed bandit executor.

        :param mOptions:                List of the m values to choose from.
        :param multiArmedBanditConfig:  Configuration for multi-armed bandit.
        """
        self.mOptions = mOptions
        self.multiArmedBanditConfig = multiArmedBanditConfig
        self.n_arms = len(self.mOptions)
        self.ni = np.zeros(self.n_arms)
        self.si = np.zeros(self.n_arms)
        self.prev_l = None
        self.i = 0
        self.gamma = 1.0
        self.rew_bias = 0.3
        # TODO

    def getNextValueOfM(self, resultsSinceLastRound):
        """
        Get the next value of m to use.

        :param resultsSinceLastRound:   Results (list of SingleRoundResults obj) since the last time an m value was chosen.

        :return: Next m value to use.
        """
        print(f'ni {self.ni}\n si {self.si}')
        # Get the observations from the previous arm pull and which arm it was
        round_latencies = [round_res.latenciesByNode for round_res in resultsSinceLastRound]
        avg_latency = np.average([max([v for k, v in (list(lats.items())[0][1]).items()]) for lats in round_latencies])

        if (self.prev_l is not None):
            # Update arm pull and reward counters
            self.ni *= self.gamma # Discounting
            self.si *= self.gamma # Discounting
            self.ni[self.prev_l] += 1
            # TODO: change how reward is calculated to include failure penalties etc.
            self.si[self.prev_l] += (self.rew_bias - avg_latency)

        if (self.prev_l is None) or (np.any(self.ni==0)):
            # Initial rounds, make sure every arm is pulled at least once
            l = np.max(np.where(self.ni==0)[0])
        else:
            # Regular decisions after initial rounds
            mui = self.si/self.ni
            nt = np.sum(self.ni)
            ucb = np.maximum(mui*(1-mui), 0.002)*np.log(nt)/self.ni
            ucb = np.sqrt(ucb)
            l = np.argmax(mui + ucb)
        
        self.prev_l = l

        print(f'Decision: {l}\n============')
        return self.mOptions[l]

    def getNextValuesOfM(self, resultsSinceLastRound, minMValueMargin):
        """
        Get the next two values of m to vote for in the distributed case.

        :param resultsSinceLastRound:   Results (SingleRoundResults obj) since the last time m values were voted for.
        :param minMValueMargin:         Minimum difference between the given m values.

        :return: Tuple of the next two values of m that the node exhibiting the given results should vote for.
        """
        pass
