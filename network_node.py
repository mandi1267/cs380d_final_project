from network_messages import *
import multiprocessing
import time
from project_utils import *
from functools import partial


def getMajorityOfBooleans(tiebreakerValue, booleansList):
    """
    Get the majority of a list of booleans, or the tiebreaker value if there were the same number of true and false
    values in the list.

    :param tiebreakerValue: Value to use (true or false) if there were the same number of trues and falses in the
                            booleans list.
    :param booleansList:    List of booleans to get the majority value of.

    :return: Value that occurred in the list most frequently, or the tiebreaker value if there was a tie.
    """
    trueCount = booleansList.count(True)
    falseCount = booleansList.count(False)

    if (trueCount == falseCount):
        return tiebreakerValue
    return trueCount > falseCount


class WaitingForResponseMsg:
    """
    Class to hold information needed when we're waiting for a message from a particular

    TODO fields will likely change as the consensus protocol is implemented
    """

    def __init__(self, awaitingForGeneralsChain):
        """
        Create the object.

        :param awaitingForGeneralsChain: List of generals that were commanders in the message we are waiting for.
        """
        self.awaitingForGeneralsChain = awaitingForGeneralsChain


class ReceivedOrDefaultInfo:
    """
    Class containing information about a message (or a default value used in place of an expected message).
    """

    def __init__(self, sendingChain, consensusValue):
        """

        :param sendingChain:    List of general ids, where the first entry is the commanding general for the whole
                                problem, the second is the commanding general for m-1, and so on.
        :param consensusValue:  Value received in the message at the given part of the recursion.
        """
        self.sendingChain = sendingChain
        self.consensusValue = consensusValue


class ConsensusMessagesTreeNode:
    """
    Data structure for storing results of the consensus operation.
    """

    def __init__(self, consensusValue, generalId):
        """
        Create a node.

        :param consensusValue:  Consensus value received by the given general id (or the default if we didn't receive a
                                message from the given general in time).
        :param generalId:       General that sent the consensus value.
        """
        self.consensusValue = consensusValue
        self.generalId = generalId
        self.children = {}

    def addChild(self, consensusValue, unprocessedGeneralIds):
        """
        Add children to the consensus message node. This is used to store results at lower levels of the recursion.

        :param consensusValue:          Consensus value received by the last general in the unprocessed general ids
                                        list.
        :param unprocessedGeneralIds:   Unprocessed general ids. These indicate which branches of the tree we still
                                        need to go down to add a node.
        """
        firstGeneralId = unprocessedGeneralIds[0]
        remainingGeneralIds = unprocessedGeneralIds[1:]

        # If the first general id is already in the childe
        if (len(remainingGeneralIds) != 0):
            if (firstGeneralId not in self.children):
                # TODO is this true? Need to revisit this if we get this error -- timeouts/delays could result in this
                #  not being true
                self.printStrWithNodePrefix(
                    "ERROR: If we have a result from a child, we should already have the parent in the tree",
                    level="ERROR")
                self.printStrWithNodePrefix(unprocessedGeneralIds, level="ERROR")
                exit(1)
            self.children[firstGeneralId].addChild(consensusValue, remainingGeneralIds)

        else:
            # TODO should we check if the first general id already exists in the children before overwriting?
            if (firstGeneralId in self.children):
                self.printStrWithNodePrefix("WARN: The general is already in the children in the tree -- overwriting",
                                            level="WARN")
            self.children[firstGeneralId] = ConsensusMessagesTreeNode(consensusValue, firstGeneralId)

    def getMinimumBranchDepth(self, expectedNodes, callingNode):
        """
        Get the minimum branch depth of this subtree.

        :return: Minimum depth of this subtree (distance from this node (including itself) to the nearest leaf node).
        """
        # TODO consider adding caching to store this and invalidate the minimum depth when the children have changed
        minChildrenDepth = 0
        expectedChildrenNodes = expectedNodes - {self.generalId}
        if (len(expectedChildrenNodes) == len(self.children)):
            if (len(self.children) != 0):
                minChildrenDepth = min(
                    [childNode.getMinimumBranchDepth(expectedChildrenNodes, callingNode) for childNode in
                     self.children.values()])
        return 1 + minChildrenDepth

    def aggregateResults(self, majorityFunction):
        """
        Aggregate the results of this node and its children using the majority function.

        :param majorityFunction:    Function that takes the majority of a list of the type of values stored in the tree.

        :return: Value obtained by applying the majority function as specified by the oral messages algorithm.
        """
        # TODO is this correct?
        return majorityFunction([self.consensusValue] + [childNode.aggregateResults(majorityFunction) for childNode in
                                                         self.children.values()])

    def __str__(self):
        # TODO clean up this print function
        baseStr = "{Node:" + str(self.generalId) + ", value:" + str(self.consensusValue)
        if (len(self.children) != 0):
            baseStr += (", children: [" + ",".join([str(childNode) for childNode in self.children.values()]) + "] },")
        else:
            baseStr += "}, "
        return baseStr


class NetworkNode:
    """
    Node that operates in the network.
    """

    def __init__(self, nodeNum, outgoingMsgQueue, outgoingMsgQueueLock, incomingMsgQueue, incomingMsgQueueLock,
                 defaultConsensusValue, sleepBetweenProcessingMs, initialConsensusTolerance, maxLatency,
                 totalNodesCount, debug=False):
        """
        Create the node.

        :param nodeNum:                     Number identifying this node.
        :param outgoingMsgQueue:            Outgoing message queue (used to send data to the network manager/other nodes
                                            from this node).
        :param outgoingMsgQueueLock:        Lock for the outgoing message queue.
        :param incomingMsgQueue:            Incoming message queue (used to send data to this node from the network
                                            manager/other nodes).
        :param incomingMsgQueueLock:        Lock for the incoming message queue.
        :param defaultConsensusValue:       Default value to use in the consensus protocol.
        :param sleepBetweenProcessingMs:    Milliseconds to sleep between checking for new messages to process.
        :param initialConsensusTolerance:   Initial consensus tolerance value (m value) to use.
        :param maxLatency:                  Maximum time in milliseconds to wait for a node's response after becoming
                                            aware that we need it.
        :param totalNodesCount:             Total number of nodes. Needed so we know what other nodes exist in our
                                            network that we should communicate with.
        """
        # TODO need to check that these are storing the address to the same queue and not creating new queues
        # Outgoing message queue (for sending to network manager or other nodes)
        self.outgoingMsgQueue = outgoingMsgQueue
        # Outgoing msg queue lock (so we don't have simultaneous reads and writes to the queue)
        self.outgoingMsgQueueLock = outgoingMsgQueueLock
        # Incoming message queue (for receiving from the network manager or other nodes)
        self.incomingMsgQueue = incomingMsgQueue
        # Outgoing msg queue lock (so we don't have simultaneous reads and writes to the queue)
        self.incomingMsgQueueLock = incomingMsgQueueLock
        # Number of this node (used as identifier)
        self.nodeNum = nodeNum
        # Consensus tolerance -- list of consensus tolerance values to test -- in centralized case, this will have 1
        # entry
        self.consensusTolerance = initialConsensusTolerance
        # Default consensus value (use in the case of timeouts or ties)
        self.defaultConsensusValue = defaultConsensusValue
        # Milliseconds that we should sleep between processing messages/timeout triggers
        self.sleepBetweenProcessingMs = sleepBetweenProcessingMs
        # Maximum time to wait for a message to be received
        self.maxLatency = maxLatency
        # List of tuples containing message signatures that we expect messages for. First element in each tuple is the
        # timeout (should use default value at this point). The second element is details about the message we are
        # waiting for.
        self.awaitingResponse = []
        # Starting time of a consensus round (used to compute latency)
        self.consensusStartTime = None
        # Number of nodes in the system (should have nodes with identifiers [0, totalNodesCount-1])
        self.totalNodesCount = totalNodesCount
        # List of received results or results injected due to timeout (ReceivedOrDefaultInfo objects)
        self.receivedResults = []
        # Tree containing results (stored in a tree mirroring the recursion). When this exists, the value is a
        # ConsensusMessagesTreeNode.
        self.consensusResultTree = None
        # True if we're in the middle of consensus, false if we're not in the middle of a consensus round
        self.executingConsensus = False
        self.pendingMessages = []
        self.debug = debug

    def printStrWithNodePrefix(self, printObj, level=""):
        if (self.debug or (level == "WARN") or (level == "ERROR")):
            print("Node " + str(self.nodeNum) + ": " + str(printObj), flush=True)

    def dummy_consensus(self):
        consensusToleranceVal = self.consensusTolerance[0]
        sleepTime = consensusToleranceVal / 10.0
        time.sleep(sleepTime)
        self.outgoingMsgQueue.put(ConsensusResultMessage(consensusToleranceVal, sleepTime, 0))

    def processMessageWhileLocked(self, msg):
        """
        Do processing of the message while holding the lock.

        :param msg: Message to process. One of the types in network_messages

        :return: True if the node should continue processing other messages, false if it should be done processing.
        """

        if (isinstance(msg, ShutdownNodeMessage)):
            return False
        if (isinstance(msg, SetMValuesMessage)):
            self.consensusTolerance = msg.nextMValues
            # TODO does anything else need to be done here?

        if (isinstance(msg, ConsensusStartMessage)):
            self.startGeneralOrDefaultConsensus(msg)

        return True

    def startGeneralOrDefaultConsensus(self, consensusStartMsg):
        """
        Function that is called once we've received a consensus start message. Should start the node to await a
        command from the general/trigger the recursive consensus protocol.

        :param consensusStartMsg:   Consensus start message that was received.
        """
        # Trigger the timer
        self.printStrWithNodePrefix("Received consensus start msg with general " + str(consensusStartMsg.mainGeneralID))
        currentTimeMillis = getCurrentTimeMillis()
        self.executingConsensus = True
        # At the beginning of the consensus round, we should remove any pending messages, they do not apply to this round
        self.awaitingResponse.clear()
        self.receivedResults.clear()
        self.pendingMessages.clear()  # TODO Is this okay to do here?
        self.consensusResultTree = None
        # Record the start time, so we can measure latency
        self.consensusStartTime = currentTimeMillis
        self.setAwaitingForResponse(currentTimeMillis, [consensusStartMsg.mainGeneralID])

    def setAwaitingForResponse(self, startWaitingTime, waitingForGenerals):
        """
        Store that we're waiting for a response with the recursion having the list of generals in waitingForGenerals as
        the commanders in the execution.

        :param startWaitingTime:    Time at which we should have triggered a timer (used to compute the time when the
                                    timeout should trigger the default value to be used)
        :param waitingForGenerals:  List of generals indicating what branch of the recursion we're in. Message that
                                    we're waiting for should have this chain of generals.
        """
        self.printStrWithNodePrefix("Added awaiting for response from " + str(waitingForGenerals))
        timeoutTime = startWaitingTime + self.maxLatency
        self.awaitingResponse.append((timeoutTime, WaitingForResponseMsg(waitingForGenerals)))

    def consensusMsgMatchesAwaitingResponse(self, msg):
        """
        Check if an incoming consensus message matches one we are waiting for, and if so, remove it from the awaiting
        list.

        :param msg: Consensus message received by the node

        :return: Details about the message that we were waiting for that this one satisfies
        """
        matchingIdx = None
        matchingMsg = None
        for awaitingMsgIdx in range(len(self.awaitingResponse)):
            awaitingMsg = self.awaitingResponse[awaitingMsgIdx]
            if (msg.commandingGeneralChain == awaitingMsg[1].awaitingForGeneralsChain):
                matchingIdx = awaitingMsgIdx
                matchingMsg = awaitingMsg[1]
                break
        if (matchingIdx is not None):
            del self.awaitingResponse[matchingIdx]
        else:
            # TODO should we discard or process it anyway? (Right now, we're not actually discarding, we're just
            #  placing in a queue to process later)
            self.printStrWithNodePrefix("WARN: Message with commanding general chain " + str(
                msg.commandingGeneralChain) + " does not match awaiting response. Discarding")
        return matchingMsg

    def handleConsensusMsg(self, msg):
        """
        Process a consensus message.

        :param msg: Consensus message received.
        """
        if (not self.executingConsensus):
            self.printStrWithNodePrefix(
                "WARN: Node " + str(self.nodeNum) + " received consensus message from node" + str(
                    msg.sourceNodeId) + " when the node didn't think it was executing consensus", level="WARN")
            return

        consensusSenderValue = msg.content
        commandingGeneralChain = msg.commandingGeneralChain[:]

        # TODO properly handle decentralized case

        matchingMsg = self.consensusMsgMatchesAwaitingResponse(msg)
        if (matchingMsg is not None):
            self.handleMsgOrDefaultFromTimeout(commandingGeneralChain, consensusSenderValue)
        else:
            self.pendingMessages.append(msg)

    def updateResultsTree(self, commandingGeneralChain, consensusValue):
        """
        Update the results tree to indicate that we should use the given consensusValue for the point in the recursion
        identified by the chain of commanding generals.

        :param commandingGeneralChain:  List of commanding generals identifying the point in the recursion that the
                                        given message is for.
        :param consensusValue:          Value that should be used for the given point in the recursion.
        """
        if (self.consensusResultTree == None):
            if (len(commandingGeneralChain) != 1):
                self.printStrWithNodePrefix("ERROR: If the consensus results tree doesn't exist, we should "
                                            "only have information from the commanding general", level="ERROR")
                exit(1)
            self.consensusResultTree = ConsensusMessagesTreeNode(consensusValue, commandingGeneralChain[0])
        else:
            self.consensusResultTree.addChild(consensusValue, commandingGeneralChain[1:])

    def handleMsgOrDefaultFromTimeout(self, commandingGeneralChain, consensusValue):
        """
        Handle the given message result (or timeout result), with the point in the recursion identified by the
        commandingGeneralChain.

        :param commandingGeneralChain:  List of generals indicating the point in the recursion that the given consensus
                                        value is for.
        :param consensusValue:          Consensus value that should be treated as received at the given point in the
                                        recursion.
        :return:
        """
        # Get the time at which the message/timeout was received
        receivedTime = getCurrentTimeMillis()
        # Update the results
        self.receivedResults.append(ReceivedOrDefaultInfo(commandingGeneralChain, consensusValue))
        self.updateResultsTree(commandingGeneralChain, consensusValue)

        # If we've reached m=0
        self.printStrWithNodePrefix(
            "Received message/timeout with " + str(consensusValue) + " and commandingGeneralChain " + str(
                commandingGeneralChain))
        self.printStrWithNodePrefix("Consensus tolerance is " + str(max(self.consensusTolerance)))
        if (len(commandingGeneralChain) > max(self.consensusTolerance)):

            # TODO Update to handle distributed case
            if (self.hasReceivedAllExpectedMessages(self.consensusTolerance[0])):
                self.sendConsensusResult(self.consensusTolerance[0],
                                         self.getDecisionFromCollectedResults(self.consensusTolerance[0]))

        else:
            # m > 0
            # Get the remaining nodes -- send to them and indicate we're also waiting for responses from them
            sendToNodes = list((set(range(self.totalNodesCount)) - set(commandingGeneralChain) - {self.nodeNum}))
            self.printStrWithNodePrefix(
                "Prev commanding general chain was " + str(commandingGeneralChain) + "; sending to " + str(sendToNodes))
            for destNodeNum in sendToNodes:
                self.sendConsensusMsg(destNodeNum, consensusValue, commandingGeneralChain)
                # Indicate that we're awaiting messages from all of the other nodes
                self.setAwaitingForResponse(receivedTime, commandingGeneralChain + [destNodeNum])

    def sendConsensusMsg(self, targetNode, consensusValue, previousCommandingGenerals):
        """
        Send a consensus message with the given value to the target node.

        :param targetNode:      Node to send the consensus message to
        :param consensusValue:  Value to include in the consensus message
        """
        self.printStrWithNodePrefix(
            "Sending consensus message " + str(consensusValue) + " with commanding general chain " + str(
                previousCommandingGenerals + [self.nodeNum]) + " to node " + str(targetNode))
        with (self.outgoingMsgQueueLock):
            self.outgoingMsgQueue.put(
                ConsensusMessage(self.nodeNum, targetNode, consensusValue, previousCommandingGenerals + [self.nodeNum]))

    def executeCommandingGeneral(self, msg):
        """
        Execute starting the consensus protocol as the commanding general.

        :param msg: Consensus start message.
        """
        self.consensusStartTime = getCurrentTimeMillis()
        # Send consensus msg then send result
        for i in range(self.totalNodesCount):
            if (i != self.nodeNum):
                # print("Node " + str(self.nodeNum) + " sending initial consensus message to " + str(i))
                self.sendConsensusMsg(i, msg.decision, [])
        self.sendConsensusResult(self.consensusTolerance[0], msg.decision)

    def processMessageWithoutLock(self, msg):
        """
        Process a message received from the network while not locked (not blocking message insertion into the queue).

        :param msg: Message received.
        """
        if (isinstance(msg, ConsensusMessage)):
            self.handleConsensusMsg(msg)

        if (isinstance(msg, TriggerConsensusCommandingGeneral)):
            self.executeCommandingGeneral(msg)

    def handleAwaitingResponseTimeout(self, awaitingResponseDetails):
        """
        Handle a message for which we have not received a response for in time.

        :param awaitingResponseDetails: Details of the message that we were awaiting but never received.
        """
        # TODO fix to handle recursive
        # Also fix for multi-m-value case
        self.printStrWithNodePrefix(
            "Timed out awaiting response for " + str(awaitingResponseDetails[1].awaitingForGeneralsChain))
        self.handleMsgOrDefaultFromTimeout(awaitingResponseDetails[1].awaitingForGeneralsChain,
                                           self.defaultConsensusValue)

    def sendConsensusResult(self, mValue, consensusResult):
        """
        Send the consensus result to the network manager.

        :param mValue:              M value that the results are for
        :param consensusResult:     Consensus result.
        """
        self.executingConsensus = False
        self.awaitingResponse.clear()
        self.pendingMessages.clear()
        self.consensusResultTree = None
        currentTime = getCurrentTimeMillis()
        consensusResultMsg = ConsensusResultMessage(mValue, currentTime - self.consensusStartTime, consensusResult)
        with self.outgoingMsgQueueLock:
            self.outgoingMsgQueue.put(consensusResultMsg)

    def hasReceivedAllExpectedMessages(self, consensusToleranceVal):
        """
        Return if we've received all of the expected messages for the given consensus tolerance value.
        All branches of the results tree should have depth of at least 1 + consensus tolerance
        :param consensusToleranceVal:
        :return:
        """
        if (self.consensusResultTree == None):
            return False
        expectedTreeNodes = set(range(self.totalNodesCount)) - {self.nodeNum}
        minBranchDepth = self.consensusResultTree.getMinimumBranchDepth(expectedTreeNodes, self.nodeNum)
        self.printStrWithNodePrefix("Minimum branch depth " + str(minBranchDepth))
        self.printStrWithNodePrefix("Results tree" + str(self.consensusResultTree))
        return (consensusToleranceVal + 1) <= minBranchDepth

    def getDecisionFromCollectedResults(self, consensusToleranceVal):
        # TODO utilize consensusToleranceValue in aggregateResults
        majorityFunction = partial(getMajorityOfBooleans, self.defaultConsensusValue)
        aggregatedResults = self.consensusResultTree.aggregateResults(majorityFunction)
        self.printStrWithNodePrefix("Results: " + str(aggregatedResults))
        return aggregatedResults

    def run(self):
        """
        Run the node by periodically checking for incoming messages. Runs until shutdown. This should be run in its
        own thread.
        """
        keepProcessing = True
        while (keepProcessing):
            time.sleep(self.sleepBetweenProcessingMs / 1000.0)
            currentTimeMillis = getCurrentTimeMillis()
            # Check for any messages that we're waiting for responses for
            timedOutMsgs = [awaitingResponseMsg for awaitingResponseMsg in self.awaitingResponse if
                            awaitingResponseMsg[0] < currentTimeMillis]
            self.awaitingResponse = [awaitingResponseMsg for awaitingResponseMsg in self.awaitingResponse if
                                     awaitingResponseMsg[0] >= currentTimeMillis]
            pendingMsgsCopy = self.pendingMessages[:]
            self.pendingMessages.clear()
            for pendingMsg in pendingMsgsCopy:
                self.handleConsensusMsg(pendingMsg)

            for awaitingResponseMsg in timedOutMsgs:
                self.handleAwaitingResponseTimeout(awaitingResponseMsg)

            if (not self.incomingMsgQueue.empty()):
                with self.incomingMsgQueueLock:
                    msg = self.incomingMsgQueue.get()
                    keepProcessing = self.processMessageWhileLocked(msg)
                self.processMessageWithoutLock(msg)


class DistributedMabNetworkNode(NetworkNode):
    """
    Version of the node that operates in the network and handles selecting the next m-value(s) to try using a
    distributed multi-armed bandit (rather than a centralized controller).
    """

    def __init__(self, nodeNum, outgoingMsgQueue, outgoingMsgQueueLock, incomingMsgQueue, incomingMsgQueueLock,
                 defaultConsensusValue, sleepBetweenProcessingMs, initialConsensusTolerance, maxLatency,
                 totalNodesCount):
        """
        Create the node.

        :param nodeNum:                     Number identifying this node.
        :param outgoingMsgQueue:            Outgoing message queue (used to send data to the network manager/other nodes
                                            from this node).
        :param outgoingMsgQueueLock:        Lock for the outgoing message queue.
        :param incomingMsgQueue:            Incoming message queue (used to send data to this node from the network
                                            manager/other nodes).
        :param incomingMsgQueueLock:        Lock for the incoming message queue.
        :param defaultConsensusValue:       Default value to use in the consensus protocol.
        :param sleepBetweenProcessingMs:    Milliseconds to sleep between checking for new messages to process.
        :param initialConsensusTolerance:   Initial consensus tolerance value (m value) to use.
        :param maxLatency:                  Maximum time in milliseconds to wait for a node's response after becoming
                                            aware that we need it.
        :param totalNodesCount:             Total number of nodes. Needed so we know what other nodes exist in our
                                            network that we should communicate with.
        """
        NetworkNode.__init__(self, nodeNum, outgoingMsgQueue, outgoingMsgQueueLock, incomingMsgQueue,
                             incomingMsgQueueLock, defaultConsensusValue, sleepBetweenProcessingMs,
                             initialConsensusTolerance, maxLatency, totalNodesCount)
