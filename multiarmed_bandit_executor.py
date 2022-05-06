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
        self.i = 0
        # TODO

    def getNextValueOfM(self, resultsSinceLastRound):
        """
        Get the next value of m to use.

        :param resultsSinceLastRound:   Results (SingleRoundResults obj) since the last time an m value was chosen.

        :return: Next m value to use.
        """
        # TODO
        m = self.mOptions[self.i]
        print(m)
        self.i = (self.i+1) % len(self.mOptions)
        return m

    def getNextValuesOfM(self, resultsSinceLastRound, minMValueMargin):
        """
        Get the next two values of m to vote for in the distributed case.

        :param resultsSinceLastRound:   Results (SingleRoundResults obj) since the last time m values were voted for.
        :param minMValueMargin:         Minimum difference between the given m values.

        :return: Tuple of the next two values of m that the node exhibiting the given results should vote for.
        """
        pass
