from network_messages import *
import queue
import threading
import time
from project_utils import *


class WaitingForResponseMsg:
    """
    Class to hold information needed when we're waiting for a message from a particular

    TODO fields will likely change as the consensus protocol is implemented
    """

    def __init__(self, awaitingForNode):
        """
        Create the object.

        :param awaitingForNode: Node that a node is awaiting a message from.
        """
        self.awaitingForNode = awaitingForNode


class NetworkNode:
    """
    Node that operates in the network.
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
        # TODO need to check that these are storing the address to the same queue and not creating new queues
        self.outgoingMsgQueue = outgoingMsgQueue
        self.outgoingMsgQueueLock = outgoingMsgQueueLock
        self.incomingMsgQueue = incomingMsgQueue
        self.incomingMsgQueueLock = incomingMsgQueueLock
        self.nodeNum = nodeNum
        self.consensusTolerance = initialConsensusTolerance
        self.defaultConsensusValue = defaultConsensusValue
        self.sleepBetweenProcessingMs = sleepBetweenProcessingMs
        self.maxLatency = maxLatency
        self.awaitingResponse = []
        self.consensusStartTime = None
        self.totalNodesCount = totalNodesCount

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
        if (isinstance(msg, ConsensusMessage)):
            # TODO handle consensus messages
            pass

        return True

    def startGeneralOrDefaultConsensus(self, consensusStartMsg):
        """
        Function that is called once we've received a consensus start message. Should start the node to await a
        command from the general/trigger the recursive consensus protocol.

        :param consensusStartMsg:   Consensus start message that was received.
        """
        # Trigger the timer
        currentTimeMillis = getCurrentTimeMillis()
        # At the beginning of the consensus round, we should remove any pending messages, they do not apply to this round
        self.awaitingResponse.clear()
        timeoutTime = currentTimeMillis + self.maxLatency
        # Record the start time, so we can measure latency
        self.consensusStartTime = currentTimeMillis
        self.awaitingResponse.append((timeoutTime, WaitingForResponseMsg(consensusStartMsg.mainGeneralID)))

    def consensusMsgMatchesAwaitingResponse(self, msg):
        """
        Check if an incoming consensus message matches one we are waiting for, and if so, remove it from the awaiting
        list.

        :param msg: Consensus message received by the node

        :return: Details about the message that we were waiting for that this one satisfies
        """
        # TODO update this to handle recursive case
        matchingIdx = None
        matchingMsg = None
        for awaitingMsgIdx in range(len(self.awaitingResponse)):
            awaitingMsg = self.awaitingResponse[awaitingMsgIdx]
            if (msg.sourceNodeId == awaitingMsg[1].awaitingForNode):
                matchingIdx = awaitingMsgIdx
                matchingMsg = awaitingMsg[1]
                break
        if (matchingIdx is not None):
            del self.awaitingResponse[matchingIdx]
        return matchingMsg

    def handleConsensusMsg(self, msg):
        """
        Process a consensus message.

        :param msg: Consensus message received.
        """

        # TODO properly handle recursion (just doing m=0 right now)
        consensusSenderValue = msg.content
        matchingMsg = self.consensusMsgMatchesAwaitingResponse(msg)
        if (matchingMsg is not None):
            # TODO Update to handle distributed case and recursive case
            self.sendConsensusResult(self.consensusTolerance[0], consensusSenderValue)

    def sendConsensusMsg(self, targetNode, consensusValue):
        """
        Send a consensus message with the given value to the target node.

        :param targetNode:      Node to send the consensus message to
        :param consensusValue:  Value to include in the consensus message
        """
        with (self.outgoingMsgQueueLock):
            self.outgoingMsgQueue.put(ConsensusMessage(self.nodeNum, targetNode, consensusValue))

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
                self.sendConsensusMsg(i, msg.decision)
        self.sendConsensusResult(self.consensusTolerance[0], msg.decision)

    def processMessageWithoutLock(self, msg):
        """
        Process a message received from the network while not locked (not blocking message insertion into the queue).

        :param msg: Message received.
        """
        if (isinstance(msg, ConsensusMessage)):
            self.handleConsensusMsg(msg)

        if (isinstance(msg, ConsensusStartMessage)):
            self.startGeneralOrDefaultConsensus(msg)

        if (isinstance(msg, TriggerConsensusCommandingGeneral)):
            self.executeCommandingGeneral(msg)

    def handleAwaitingResponseTimeout(self, awaitingResponseDetails):
        """
        Handle a message for which we have not received a response for in time.

        :param awaitingResponseDetails: Details of the message that we were awaiting but never received.
        """
        # TODO fix to handle recursive
        # Also fix for multi-m-value case
        self.sendConsensusResult(self.consensusTolerance[0], self.defaultConsensusValue)

    def sendConsensusResult(self, mValue, consensusResult):
        """
        Send the consensus result to the network manager.

        :param mValue:              M value that the results are for
        :param consensusResult:     Consensus result.
        """
        currentTime = getCurrentTimeMillis()
        consensusResultMsg = ConsensusResultMessage(mValue, currentTime - self.consensusStartTime, consensusResult)
        with self.outgoingMsgQueueLock:
            self.outgoingMsgQueue.put(consensusResultMsg)

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
