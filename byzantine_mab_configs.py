import joblib  # https://joblib.readthedocs.io/en/latest/persistence.html
import yaml

RUN_CONFIG_FILE_YAML_NAME = "run_config_file"
MULTI_ARMED_BANDIT_CONFIG_FILE_YAML_NAME = "multi_armed_bandit_config_file"
ROUND_CONFIG_FILE_YAML_NAME = "round_config_file"
NETWORK_LATENCY_CONFIG_FILE_YAML_NAME = "network_latency_config_file"
BYZANTINE_ERROR_CONFIG_FILE_YAML_NAME = "byzantine_error_config_file"
DISTRIBUTED_MAB_CONFIG_FILE_YAML_NAME = "distributed_mab_config_file"


class SuperConfig:
    """
    Configuration object that maintains all other configs
    """

    def __init__(self, runConfigFile, multiArmedBanditConfigFile, roundConfigFile, networkLatencyConfigFile,
                 byzantineErrorConfigFile, distributedMABConfigFile):
        """
        Set the filenames for the sub-configs.

        :param runConfigFile:               File name for the general experiment setup.
        :param multiArmedBanditConfigFile:  File name for the multi-armed bandit configuration parameters.
        :param roundConfigFile:             File name for the round configuration parameters.
        :param networkLatencyConfigFile:    File name for the network latency configuration parameters.
        :param byzantineErrorConfigFile:    File name for the byzantine fault configuration parameters.
        :param distributedMABConfigFile:    File name for the distributed multi-armed bandit configuration (only used
                                            in the decentralized case).
        """
        self.runConfigFile = runConfigFile
        self.multiArmedBanditConfigFile = multiArmedBanditConfigFile
        self.roundConfigFile = roundConfigFile
        self.networkLatencyConfigFile = networkLatencyConfigFile
        self.byzantineErrorConfigFile = byzantineErrorConfigFile
        self.distributedMABConfigFile = distributedMABConfigFile

    def getRunConfig(self):
        return joblib.load(self.runConfigFile)

    def getMultiArmedBanditConfig(self):
        return joblib.load(self.multiArmedBanditConfigFile)

    def getRoundConfig(self):
        return joblib.load(self.roundConfigFile)

    def getNetworkLatencyConfig(self):
        return joblib.load(self.networkLatencyConfigFile)

    def getByzantineErrorConfig(self):
        return joblib.load(self.byzantineErrorConfigFile)

    def getDistributedMABConfig(self):
        return joblib.load(self.distributedMABConfigFile)


class RunConfig:
    """
    Configuration object containing the core parameters needed to execute the experiments.
    """

    def __init__(self, numConsensusRounds, numNodes, possibleMValues, useCentralizedMultiArmedBandit,
                 sleepBetweenNodeProcessingMs):
        """
        Initialize the config.

        :param numConsensusRounds:              Number of rounds of consensus that should be executed.
        :param numNodes:                        Number of nodes in the system.
        :param possibleMValues:                 Possible m values that can be used by the nodes.
        :param useCentralizedMultiArmedBandit:  True if the m values to use should be determined using a centralized
                                                controller, false if the m values should be decided in a distributed
                                                manner.
        :param sleepBetweenNodeProcessingMs:    Amount of time in milliseconds for a node to sleep between checks of its
                                                queue
        """
        self.numConsensusRounds = numConsensusRounds
        self.numNodes = numNodes
        self.possibleMValues = possibleMValues
        self.useCentralizedMultiArmedBandit = useCentralizedMultiArmedBandit
        self.sleepBetweenNodeProcessingMs = sleepBetweenNodeProcessingMs


class MultiArmedBanditConfig:
    """
    Configuration object containing the parameters used in determining which m values to use based on detected
    failures and latencies in consensus rounds.
    """

    def __init__(self):
        # TODO fill in
        pass


class RoundConfig:
    """
    Configuration for the rounds
    """

    def __init__(self, roundsPerObservationPeriod):
        """
        Initialize the config.

        :param roundsPerObservationPeriod:  Number of rounds of consensus in each observation period. The m-value
                                            should stay constant for a single observation period.
        """
        self.roundsPerObservationPeriod = roundsPerObservationPeriod


class NetworkLatencyConfig:
    """
    Network latency configuration.
    """

    def __init__(self, averageLatencyMs, latencyStdDevMs, maxLatencyMs):
        """
        Initialize the network latency configuration.

        :param averageLatencyMs:    Average latency for a single message.
        :param latencyStdDevMs:     Standard deviation for latency for a single message.
        :param maxLatencyMs:        Max latency for a single message (needed since sampling from a normal distribution
                                    isn't bounded, even if extremes are unlikely).
        """
        self.averageLatencyMs = averageLatencyMs
        self.latencyStdDevMs = latencyStdDevMs
        self.maxLatencyMs = maxLatencyMs


class ByzantineErrorConfig:
    """
    Byzantine error configuration.
    """

    def __init__(self, consensusRoundToSetMValue, percentDropMessage, defaultConsensusValue):
        """

        :param consensusRoundToSetMValue:   Dictionary of consensus round number to a number of faulty nodes that
                                            should be used. This gives the consensus round at which the matched value of
                                            m should be used.
        :param percentDropMessage:          Percent of the time that, when a node should exhibit byzantine failure, it
                                            will simply not publish a message. The remaining percent of the time, it
                                            will give random output. We won't have the primary general ever drop the
                                            message, because then the consensus round would not ever begin.
        :param defaultConsensusValue:       Value that should be used if there is no majority vote in consensus.
        """
        self.consensusRoundToSetMValue = consensusRoundToSetMValue
        self.percentDropMessage = percentDropMessage
        # Do we just want booleans for consensus?
        self.defaultConsensusValue = defaultConsensusValue


class DistributedMABConfig:
    """
    Configuration for a distributed execution of multi-armed bandits.
    """

    def __init__(self, minMValueMargin, decentralizedMultiArmedBanditFaultToleranceValue, defaultMValuePair):
        """
        Initialize the distributed multi-armed bandit configuraiton.

        :param minMValueMargin:                                     Minimum difference between the two m values to try
                                                                    against each other in the distributed execution.
        :param decentralizedMultiArmedBanditFaultToleranceValue:    Value of m that should be used when deciding the
                                                                    next values of m to use.
        :param defaultMValuePair:                                   Pair of m values that should be used if no m-values
                                                                    sent.
        """
        self.minMValueMargin = minMValueMargin
        # M value to use when choosing the next m value
        self.decentralizedMultiArmedBanditFaultToleranceValue = decentralizedMultiArmedBanditFaultToleranceValue
        self.defaultMValuePair = defaultMValuePair


def readSuperConfigYaml(yamlConfigFileName):
    """
    Read the super-config from the given YAML file with the data for the superconfig.

    :param yamlConfigFileName:  File name of the YAML file containing the file names of the individual configs.

    :return: SuperConfig containing file names for all configuration data.
    """
    with open(yamlConfigFileName, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
        return SuperConfig(data_loaded[RUN_CONFIG_FILE_YAML_NAME],
                           data_loaded[MULTI_ARMED_BANDIT_CONFIG_FILE_YAML_NAME],
                           data_loaded[ROUND_CONFIG_FILE_YAML_NAME],
                           data_loaded[NETWORK_LATENCY_CONFIG_FILE_YAML_NAME],
                           data_loaded[BYZANTINE_ERROR_CONFIG_FILE_YAML_NAME],
                           data_loaded[DISTRIBUTED_MAB_CONFIG_FILE_YAML_NAME])
