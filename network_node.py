from network_messages import *
import queue
import threading
import time


class NetworkNode:
    """
    Node that operates in the network.
    """

    def __init__(self, nodeNum, outgoingMsgQueue, outgoingMsgQueueLock, incomingMsgQueue, incomingMsgQueueLock,
                 defaultConsensusValue, sleepBetweenProcessingMs):
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
        """
        # TODO need to check that these are storing the address to the same queue and not creating new queues
        self.outgoingMsgQueue = outgoingMsgQueue
        self.outgoingMsgQueueLock = outgoingMsgQueueLock
        self.incomingMsgQueue = incomingMsgQueue
        self.incomingMsgQueueLock = incomingMsgQueueLock
        self.nodeNum = nodeNum
        self.defaultConsensusValue = defaultConsensusValue
        self.sleepBetweenProcessingMs = sleepBetweenProcessingMs

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

    def processMessageWithoutLock(self, msg):
        # TODO
        if (isinstance(msg, ConsensusMessage)):
            # TODO handle consensus messages
            pass

    def run(self):
        """
        Run the node by periodically checking for incoming messages. Runs until shutdown. This should be run in its
        own thread.
        """
        keepProcessing = True
        while (keepProcessing):
            time.sleep(self.sleepBetweenProcessingMs / 1000.0)
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
                 defaultConsensusValue, sleepBetweenProcessingMs):
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
        """
        NetworkNode.__init__(self, nodeNum, outgoingMsgQueue, outgoingMsgQueueLock, incomingMsgQueue,
                             incomingMsgQueueLock, defaultConsensusValue, sleepBetweenProcessingMs)
