class ConsensusMessage:
    """
    Message passed from node to node in the consensus protocol.
    """

    def __init__(self, sourceNodeId, destNodeId, content):
        """
        Create the message.

        :param sourceNodeId:    Node id of the node that sent the message.
        :param destNodeId:      Node id of the node that should receive the message.
        :param content:         Contents of the message (type may vary).
        """
        self.sourceNodeId = sourceNodeId
        self.destNodeId = destNodeId
        self.content = content


class ConsensusResultMessage:
    """
    Message from a node to the network manager conveying the results of the consensus protocol for a particular m value.
    """

    def __init__(self, mValue, latency, consensusOutcome):
        """
        Create the message.

        :param mValue:              M value that the results are for.
        :param latency:             Latency experienced when reaching consensus.
        :param consensusOutcome:    Outcome of the consensus protocol (agreed-upon value).
        """
        self.mValue = mValue
        self.latency = latency
        self.consensusOutcome = consensusOutcome


class DistributedConsensusResultMessage:
    """
    Message from a node to the network manager conveying the results of the consensus protocol for multiple m values.
    """

    def __init__(self, individualConsensusResults):
        """
        Create the message.

        :param individualConsensusResults:  List of ConsensusResultMessages (one per m-value).
        """
        self.individualConsensusResults = individualConsensusResults


class SetMValuesMessage:
    """
    Message from the network manager to the nodes used to set the m-value(s) to be used in the consensus protocol.
    """

    def __init__(self, nextMValues):
        """
        Create the message.

        :param nextMValues: Next m value(s) to use in the consensus protocol. Either a positive integer or a list of
                            positive integers.
        """
        self.nextMValues = nextMValues

class ShutdownNodeMessage:
    """
    Message from the network manager to a node that indicates that the node should stop running the processing thread.
    """

    def __init__(self):
        pass
