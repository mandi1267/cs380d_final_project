
class SingleRoundResults:
    """
    Results for a single round of communication.
    """

    def __init__(self, latenciesByNode, consensusesByNode, trueConsensus, didFail):
        """
        Results for a single round of consensus

        :param latenciesByNode:     Map of m-value used to map of node # to latency for the node
        :param consensusesByNode:   Map of m-value used to map of node # to value determined in consensus
        :param trueConsensus:       True value that should've been agreed on
        :param didFail:             Map of failure results. Key is m-value used. Value is true if the nodes reached
                                    different conclusions, false if they all reached the same output
        """
        self.latenciesByNode = latenciesByNode
        self.consensusesByNode = consensusesByNode
        self.trueConsensus = trueConsensus
        self.didFail = didFail


class FullResults:
    """
    Results for the full experiment.
    """

    def __init__(self):
        # Each of these contain the information for the round corresponding to the list index
        # Results (SingleRoundResults) for each round of consensus
        self.perRoundResults = []

        # Number of faulty nodes in the given round
        self.trueFaultyNodesCount = []

        # Value of M used by the consensus algorithm
        self.consensusFaultToleranceChosen = []

        # List of results (SingleRoundResults) since the last time an m-value was chosen
        self.resultsSinceLastDecision = []

    def addRoundResults(self, singleRoundResults, trueFaultyNodesCount, consensusFaultToleranceChosen):
        """
        Add results for a round of consensus.

        :param singleRoundResults:              SingleRoundResults object for the consensus round.
        :param trueFaultyNodesCount:            Number of faulty nodes.
        :param consensusFaultToleranceChosen:   Value of m used by the consensus algorithm.
        """
        self.perRoundResults.append(singleRoundResults)
        self.trueFaultyNodesCount.append(trueFaultyNodesCount)
        self.consensusFaultToleranceChosen.append(consensusFaultToleranceChosen)

        self.resultsSinceLastDecision.append(singleRoundResults)

    def getAndResetResultsSinceLastDecision(self):
        """
        Get the results since the last m value chosen and clear the results since the last m value (assumes we will have
        incorporated all information from these rounds into our learning approach).

        :return: List of results (SingleRoundResults) since the last m value chosen and clear the results since the
        last m value
        """
        resultsToReturn = list(self.resultsSinceLastDecision)
        self.resultsSinceLastDecision.clear()
        return resultsToReturn