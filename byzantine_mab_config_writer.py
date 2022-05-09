import joblib
import os
import sys
from byzantine_mab_configs import *
import yaml
import math
import random
import numpy as np

YAML_FILE_SUFFIX = "_super_config"
YAML_FILE_EXT = ".yaml"
PKL_FILE_EXT = ".pkl"
RUN_CONFIG_FILE_SUFFIX = "_run_config_file"
MULTI_ARMED_BANDIT_CONFIG_FILE_SUFFIX = "_multi_armed_bandit_config_file"
ROUND_CONFIG_FILE_SUFFIX = "_round_config_file"
NETWORK_LATENCY_CONFIG_FILE_SUFFIX = "_network_latency_config_file"
BYZANTINE_ERROR_CONFIG_FILE_SUFFIX = "_byzantine_error_config_file"
DISTRIBUTED_MAB_CONFIG_FILE_SUFFIX = "_distributed_mab_config_file"


def writeConfig(fileName, configObj):
    """
    Write a configuration object to the given file.

    :param fileName:    File to write the configuration to
    :param configObj:   Configuration object to write
    """
    joblib.dump(configObj, fileName)


def createConfigs():
    """

    :return: Tuple of (RunConfig, MultiArmedBanditConfig, RoundConfig, NetworkLatencyConfig, ByzantineErrorConfig, DistributedMABConfig)
    """

    numNodes = 64
    maxFaulty = 21  # (numNodes-1)/3

    possibleMValues = [1, 6, 11, 16, 21]  # TODO is this good?
    useCentralizedMultiArmedBandit = True

    # TODO these are kind of arbitrary, but don't reaaaally affect the results, so that's okay
    averageLatencyMs = 20
    latencyStdDevMs = 7
    maxLatencyMs = 50
    sleepBetweenNodeProcessingMs = 1  # Somewhat arbitrary, changed from 0.1

    percentDropMessage = 0.0
    defaultConsensusValue = False

    # Not actually used
    minMValueMargin = 5
    decentralizedMultiArmedBanditFaultToleranceValue = max(possibleMValues)
    defaultMValuePair = [6, 16]

    # TODO These are the big unknowns -- need to discuss these
    roundsPerObservationPeriod = 15  # TODO replace this
    averageObsPeriodsToConvergence = 4  # TODO replace this
    conservativeObsPeriodsToConvergence = 2 * averageObsPeriodsToConvergence
    numberOfTrueMs = 16  # TODO replace this

    roundForNextM = 0
    consensusRoundToSetMValue = {}
    possibleMValuePersistenceLengths = list(np.array(range(conservativeObsPeriodsToConvergence - (averageObsPeriodsToConvergence // 2),
                                             conservativeObsPeriodsToConvergence + (averageObsPeriodsToConvergence // 2)), dtype=int)\
                                                 * roundsPerObservationPeriod)
    for mValIdx in range(numberOfTrueMs):
        nextMValue = random.randint(0, maxFaulty)
        consensusRoundToSetMValue[roundForNextM] = nextMValue
        roundForNextM += random.choice(possibleMValuePersistenceLengths)

    print("Rounds to set m values: " + str(consensusRoundToSetMValue))

    numConsensusRounds = max(roundForNextM,
                             roundsPerObservationPeriod * conservativeObsPeriodsToConvergence * numberOfTrueMs)

    runConfig = RunConfig(numConsensusRounds, numNodes, possibleMValues, useCentralizedMultiArmedBandit,
                          sleepBetweenNodeProcessingMs)
    multiArmedBanditConfig = MultiArmedBanditConfig()  # TODO Sai, I left this in case the multi-armed bandit piece needs parameters. Nothing needed for now
    roundConfig = RoundConfig(roundsPerObservationPeriod)
    networkLatencyConfig = NetworkLatencyConfig(averageLatencyMs, latencyStdDevMs, maxLatencyMs)
    byzantineErrorConfig = ByzantineErrorConfig(consensusRoundToSetMValue, percentDropMessage, defaultConsensusValue)
    distributedMABConfig = DistributedMABConfig(minMValueMargin, decentralizedMultiArmedBanditFaultToleranceValue,
                                                defaultMValuePair)

    return (runConfig, multiArmedBanditConfig, roundConfig, networkLatencyConfig, byzantineErrorConfig,
            distributedMABConfig)

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Expected arg for directory for configs and arg for config file prefix")

    (runConfig, multiArmedBanditConfig, roundConfig, networkLatencyConfig, byzantineErrorConfig,
     distributedMABConfig) = createConfigs()

    configDir = sys.argv[1]
    baseFilePrefix = sys.argv[2]

    runConfigBaseName = baseFilePrefix + RUN_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    runConfigFileName = os.path.join(configDir, runConfigBaseName)
    writeConfig(runConfigFileName, runConfig)

    multiArmedBanditConfigBaseName = baseFilePrefix + MULTI_ARMED_BANDIT_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    multiArmedBanditConfigFileName = os.path.join(configDir, multiArmedBanditConfigBaseName)
    writeConfig(multiArmedBanditConfigFileName, multiArmedBanditConfig)

    roundConfigBaseName = baseFilePrefix + ROUND_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    roundConfigFileName = os.path.join(configDir, roundConfigBaseName)
    writeConfig(roundConfigFileName, roundConfig)

    networkLatencyConfigBaseName = baseFilePrefix + NETWORK_LATENCY_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    networkLatencyConfigFileName = os.path.join(configDir, networkLatencyConfigBaseName)
    writeConfig(networkLatencyConfigFileName, networkLatencyConfig)

    byzantineErrorConfigBaseName = baseFilePrefix + BYZANTINE_ERROR_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    byzantineErrorConfigFileName = os.path.join(configDir, byzantineErrorConfigBaseName)
    writeConfig(byzantineErrorConfigFileName, byzantineErrorConfig)

    distributedMABConfigBaseName = baseFilePrefix + DISTRIBUTED_MAB_CONFIG_FILE_SUFFIX + PKL_FILE_EXT
    distributedMABConfigFileName = os.path.join(configDir, distributedMABConfigBaseName)
    writeConfig(distributedMABConfigFileName, distributedMABConfig)

    yamlFileBaseName = baseFilePrefix + YAML_FILE_SUFFIX + YAML_FILE_EXT
    yamlFileName = os.path.join(configDir, yamlFileBaseName)

    yamlOutData = {
        RUN_CONFIG_FILE_YAML_NAME: runConfigFileName,
        MULTI_ARMED_BANDIT_CONFIG_FILE_YAML_NAME: multiArmedBanditConfigFileName,
        ROUND_CONFIG_FILE_YAML_NAME: roundConfigFileName,
        NETWORK_LATENCY_CONFIG_FILE_YAML_NAME: networkLatencyConfigFileName,
        BYZANTINE_ERROR_CONFIG_FILE_YAML_NAME: byzantineErrorConfigFileName,
        DISTRIBUTED_MAB_CONFIG_FILE_YAML_NAME: distributedMABConfigFileName
    }

    # TODO verify that this is right
    with open(yamlFileName, 'w') as outfile:
        yaml.dump(yamlOutData, outfile)
