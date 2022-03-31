# class NetworkManager:
#
#     def __init__(self, nodes):
#         self.nodes = nodes
#
#
#     def sendMessage(self, senderId, destId, message):
#         # TODO where to put threading to get accurate latency
#         # TODO
#         # TODO need to inject errors/latency
#         if (self.maybeSimulateMessageFailure(senderId, destId, message)):
#             return
#         self.simulateLatency(senderId, destId)
#         maybeCorruptedMessage = self.optionallyCorruptMessage(senderId, destId, message)
#         self.nodes[destId].receiveMessage(senderId, maybeCorruptedMessage)
#         # TODO need to
#
#     def simulateLatency(self, senderId, destId):
#         # TODO
#         pass
#
#     def optionallyCorruptMessage(self, senderId, destId, message):
#         # TODO
#         # Alter this to actually corrupt
#         return message
#
#     def maybeSimulateMessageFailure(self, senderId, destId, message):
#         #TODO
#         return false

class NetworkManager:
    """
    Object that is used to start up and communicate with the individual nodes in the system.
    """

    def __init__(self, networkLatencyConfig, numNodes, defaultConsensusValue, initialConsensusTolerance,
                 byzantineFaultDropMessagePercent, useCentralizedMab):

        """
        Initialize the network
        :param networkLatencyConfig:                Configuration for the network latency.
        :param numNodes:                            Number of nodes to have in the network.
        :param defaultConsensusValue:               Default value to use when no value provided in consensus.
        :param initialConsensusTolerance:           Initial m value(s) to use in reaching consensus. Tuple of 2 entries
                                                    if distributed, single value if centralized.
        :param byzantineFaultDropMessagePercent:    When a node is exhibiting byzantine faults, percent of the time
                                                    that it should simply drop messages. The remaining percent, it will
                                                    return a (possibly incorrect) value.
        :param useCentralizedMab:                   True if a centralized multi-armed bandit is used, false if each
                                                    node should use its own data to vote and then use consensus to
                                                    agree on the next pair of m-values that they should all use.
        """
        self.networkLatencyConfig = networkLatencyConfig
        self.numFaultyNodes = 0
        self.numNodes = numNodes
        self.defaultConsensusValue = defaultConsensusValue
        self.consensusTolerance = initialConsensusTolerance
        self.byzantineFaultDropMessagePercent = byzantineFaultDropMessagePercent
        self.useCentralizedMab = useCentralizedMab
        # TODO initialize nodes

    def changeNumFaultyNodes(self, newNumFaultyNodes):
        """
        Change the number of faulty nodes that should exist in the system.

        :param newNumFaultyNodes:   Number of faulty nodes that should exist in the system.
        """
        if (self.numNodes <= (2 * newNumFaultyNodes)):
            print "The number of nodes in this system (" + str(
                self.numNodes) + ") is less than the minimum needed to tolerate " + str(
                newNumFaultyNodes) + " faulty nodes"
        self.numFaultyNodes = newNumFaultyNodes

    def updateFaultyNodes(self):
        """
        Set the nodes that should behave incorrectly in the next consensus round. Number of these should equal
        self.numFaultyNodes
        """
        # TODO
        pass

    def startConsensus(self, trueConsensusValue):
        """
        Trigger a round of consensus. The general (if non-faulty) should send the trueConsensusValue.

        :param trueConsensusValue:  Value that the general should send.
        # TODO maybe merge this with getNodeLatenciesAndDecisions instead of making them 2 separate calls
        """
        self.trueConsensusValue = trueConsensusValue
        # TODO pick a node to act as general to start the consensus protocol
        # TODO Actually execute the consensus protocol

    def getNodeLatenciesAndDecisions(self):
        """
        Wait for the nodes to each come to a decision and return the results.

        :return: Tuple of latencies and consensuses. Latencies is map of m-value to map of node # to latency
        experienced. Consensuses is map of m-value to map of node # to the decision reached. For decentralized case,
        there will be two keys in outer map (2 m values) for both consensuses and latencies. For centralized case,
        there will be one key in outer map (1 m value) for both consensuses and latencies.
        """
        # TODO get the latencies and decisions from each node
        pass

    def setConsensusTolerance(self, newConsensusTolerance):
        """
        (Centralized case only) Set the m value to use for the next observation period. Need to propagate this to each
        of the nodes.

        :param newConsensusTolerance: New m value to use for the next observation period.
        """
        self.consensusTolerance = newConsensusTolerance
        # TOOD propagate to the nodes

    def haveDistributedNodesChooseNextMValues(self):
        """
        (Distributed case only) Have each node compute votes for the next two m values to use and then trigger a
        round of consensus to get the nodes to agree on the next two m values.

        :return: Next two m-values to use in the next observation period.
        """

        # TODO
        # Temporarily switch the m-value to be very conservative
        # Trigger a single node to start consensus for deciding the next m values
        # It will send its m values which will trigger all othe rnodes to calculate their votes for m values based on
        # their most recent results
        # Once consensus is reached, get the two m values. Set this for all nodes (ensure byzantine faults aren't
        # affecting the experimental results by making different nodes use different m values)
        # Set the m-values to the new value (no longer use conservative one)
        pass

