from network_messages import *
from network_node import *
import queue
import random
import threading
import copy
import time
import numpy as np


class NetworkManager:
    """
    Object that is used to start up and communicate with the individual nodes in the system.
    """

    def __init__(self, networkLatencyConfig, numNodes, defaultConsensusValue, initialConsensusTolerance,
                 byzantineFaultDropMessagePercent, useCentralizedMab, sleepBetweenNodeProcessingMs):

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

        self.currentFaultyNodes = []

        self.fromNodeQueues = []
        self.fromNodeQueueLocks = []
        self.toNodeQueues = []
        self.toNodeQueueLocks = []
        self.nodes = []
        self.pendingMessages = [queue.PriorityQueue for i in range(self.numNodes)]
        self.resultsByNode = {}
        self.threads = []
        for i in range(self.numNodes):
            nextFromNodeQueue = queue.Queue()
            nextFromNodeQueueLock = threading.Lock()
            self.fromNodeQueues.append(nextFromNodeQueue)
            self.fromNodeQueueLocks.append(nextFromNodeQueueLock)
            nextToNodeQueue = queue.Queue()
            nextToNodeQueueLock = threading.Lock()
            self.toNodeQueueLocks.append(nextToNodeQueueLock)
            self.toNodeQueues.append(nextToNodeQueue)

            threadingFunction = None
            if (useCentralizedMab):
                node = NetworkNode(i, nextFromNodeQueue, nextFromNodeQueueLock, nextToNodeQueue, nextToNodeQueueLock,
                                   defaultConsensusValue, sleepBetweenNodeProcessingMs)
                threadingFunction = NetworkNode.run
            else:
                node = DistributedMabNetworkNode(i, nextFromNodeQueue, nextFromNodeQueueLock, nextToNodeQueue,
                                                 nextToNodeQueueLock, defaultConsensusValue,
                                                 sleepBetweenNodeProcessingMs)
                threadingFunction = DistributedMabNetworkNode.run
            self.nodes.append(node)

            # TODO check if this is the proper way to start a thread using a class function
            nodeThread = threading.Thread(threadingFunction, args=(node,))
            self.threads.append(nodeThread)
            nodeThread.run()

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
        self.currentFaultyNodes = random.sample(range(self.numNodes), self.numFaultyNodes)

    def startConsensusAndGetNodeLatenciesAndDecisions(self, trueConsensusValue):
        """
        Trigger a round of consensus and wait for the nodes to each come to a decision and return the results. The
        general (if non-faulty) should send the trueConsensusValue.

        :param trueConsensusValue:  Value that the general should send.

        :return: Tuple of latencies and consensuses. Latencies is map of m-value to map of node # to latency
        experienced. Consensuses is map of m-value to map of node # to the decision reached. For decentralized case,
        there will be two keys in outer map (2 m values) for both consensuses and latencies. For centralized case,
        there will be one key in outer map (1 m value) for both consensuses and latencies.
        """
        self.trueConsensusValue = trueConsensusValue

        # TODO pick a node to act as general to start the consensus protocol
        # TODO Actually execute the consensus protocol

        self.waitForNodeResponses()

        # Extract the latencies and decisions from the node result messages
        if (self.useCentralizedMab):
            mValue = self.consensusTolerance
            latencyInnerDict = {}
            consensusValInnerDict = {}
            for nodeNum, results in self.resultsByNode.items():
                latencyInnerDict[nodeNum] = results.latency
                consensusValInnerDict[nodeNum] = results.consensusOutcome

            latencies = {mValue, latencyInnerDict}
            consensuses = {mValue, consensusValInnerDict}

        else:
            latencies = {}
            consensuses = {}

            for nodeNum, results in self.resultsByNode.items():
                for mValueResult in results:
                    mVal = mValueResult.mValue
                    latencies[mVal][nodeNum] = mValueResult.latency
                    consensuses[mVal][nodeNum] = mValueResult.consensusOutcome

        self.resultsByNode.clear()
        return (latencies, consensuses)

    def checkAllNodesDeliveredResults(self):
        """
        Check if all nodes have delivered their consensus results

        :return: True if all nodes have delivered their consensus results, false if we're still waiting for results
        """
        return len(self.resultsByNode) == self.numNodes

    def waitForNodeResponses(self):
        """
        Process the node messages while we haven't yet gotten results for all nodes.
        """
        while (not self.checkAllNodesDeliveredResults()):
            self.processMessages()

    def processMessages(self):
        """
        Run one iteration of processing messages. Check for messages incoming from each node and then check if any
        messages should be delivered to the nodes (and if so, deliver them).
        :return:
        """
        for i in range(self.numNodes):
            incomingQueueLock = self.fromNodeQueueLocks[i]
            incomingQueue = self.fromNodeQueues[i]

            # Check for incoming messages
            while not incomingQueue.empty():
                with incomingQueueLock:
                    incomingMsg = incomingQueue.get()
                    if (isinstance(incomingMsg, ConsensusMessage)):
                        self.enqueueMessageToDest(incomingMsg, i, incomingMsg.destNodeId)
                    elif (isinstance(incomingMsg, ConsensusResultMessage) or
                          isinstance(incomingMsg, DistributedConsensusResultMessage)):
                        self.resultsByNode[i] = incomingMsg

            # Process messages that are pending for the current node
            if (not self.pendingMessages[i].empty()):
                outgoingQueueLock = self.toNodeQueueLocks[i]
                outgoingQueue = self.toNodeQueues[i]

                while (True):
                    # Get the first message to be delivered and see if it should be delivered yet (see if delivery tine is less than current time)
                    # TODO verify that the priority queue returns the smallest element first
                    nextMsg = self.pendingMessages[i].get()
                    if (nextMsg[0] < self.getCurrentTimeMillis()):
                        with outgoingQueueLock:
                            outgoingQueue.put(nextMsg[1])
                    else:
                        # If the message isn't ready to be delivered, put it back in the queue and break
                        self.pendingMessages[i].put(nextMsg)
                        break

    def getCurrentTimeMillis(self):
        """
        Get the current time, in milliseconds.

        :return: current time in milliseconds.
        """
        return time.time() * 1000

    def getMessageDelay(self):
        """
        Get the delay that should be used for the next message. Based on sampling from a normal distribution (with
        bounds added for min/max).

        :return: Delay that should be imposed before delivering a message.
        """
        avgLatency = self.networkLatencyConfig.averageLatencyMs
        stdDevLatency = self.networkLatencyConfig.latencyStdDevMs
        maxLatency = self.networkLatencyConfig.maxLatencyMs
        randomLatency = np.random.normal(avgLatency, stdDevLatency)

        return max(0, min(maxLatency, randomLatency))

    def enqueueMessageToDest(self, message, sender, dest):
        """
        Enqueue the given message to the destination's pending queue. Add byzantine faults and latency as appropriate.

        :param message: Message to deliver (uncorrupted).
        :param sender:  Id of the node that sent the message.
        :param dest:    Id of the node that should receive the message.
        """
        passMsg = copy.deepcopy(message)
        if (sender in self.currentFaultyNodes):
            if (random.uniform(0, 1) < self.byzantineFaultDropMessagePercent):
                # Simulate a byzantine fault in which the message is dropped
                return
            else:
                passMsg.content = self.corruptMessageContents(passMsg.content)

        currentTime = self.getCurrentTimeMillis()
        msgDelay = self.getMessageDelay()
        deliveryTime = currentTime + msgDelay
        self.pendingMessages[dest].put(item=(deliveryTime, passMsg))

    def corruptMessageContents(self, contents):
        """
        Corrupt the contents of a message (to simulate Byzantine faults).

        :param contents: Contents of the message, uncorrputed.

        :return: Corrupted message contents.
        """
        if (isinstance(contents, bool)):
            return bool(random.getrandbits(1))
        else:
            print "Corrupt message not implemented for type " + str(type(contents))
            exit(1)

    def setConsensusTolerance(self, newConsensusTolerance):
        """
        (Centralized case only) Set the m value to use for the next observation period. Need to propagate this to each
        of the nodes.

        :param newConsensusTolerance: New m value to use for the next observation period.
        """
        self.consensusTolerance = newConsensusTolerance
        setMValuesMessage = SetMValuesMessage([self.consensusTolerance])
        for i in range(self.numNodes):
            with self.toNodeQueueLocks[i]:
                self.toNodeQueues[i].put(setMValuesMessage)
        anyQueuesNotProcessed = True
        while (anyQueuesNotProcessed):
            anyQueuesNotProcessed = False
            for i in range(self.numNodes):
                with self.toNodeQueueLocks[i]:
                    toNodeQueue = self.toNodeQueues[i]
                    if (not toNodeQueue.empty()):
                        anyQueuesNotProcessed = True
                        break

    def haveDistributedNodesChooseNextMValues(self):
        """
        (Distributed case only) Have each node compute votes for the next two m values to use and then trigger a
        round of consensus to get the nodes to agree on the next two m values.

        :return: Next two m-values to use in the next observation period.
        """

        # TODO
        # TODO Temporarily switch the m-value to be very conservative
        # TODO Trigger a single node to start consensus for deciding the next m values
        # It will send its m values which will trigger all othe rnodes to calculate their votes for m values based on
        # their most recent results

        # Once consensus is reached, get the two m values. Set this for all nodes (ensure byzantine faults aren't
        # affecting the experimental results by making different nodes use different m values)
        self.waitForNodeResponses()

        # TODO Get m-values from responses
        mValues = None  # TODO

        # Set the m-values to the new value (no longer use conservative one)
        self.setConsensusTolerance(mValues)

    def shutdown(self):
        """
        Shutdown the node threads.
        """
        shutdownMessage = ShutdownNodeMessage()
        for i in range(self.numNodes):
            with self.toNodeQueueLocks[i]:
                self.toNodeQueues[i].put(shutdownMessage)
        anyQueuesNotProcessed = True
        while (anyQueuesNotProcessed):
            anyQueuesNotProcessed = False
            for i in range(self.numNodes):
                with self.toNodeQueueLocks[i]:
                    toNodeQueue = self.toNodeQueues[i]
                    if (not toNodeQueue.empty()):
                        anyQueuesNotProcessed = True
                        break

        for nodeThread in self.threads:
            nodeThread.join()