import joblib
import os
import sys
from byzantine_mab_configs import *
import yaml
import math

YAML_FILE_SUFFIX="_super_config"
YAML_FILE_EXT=".yaml"
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

if __name__=="__main__":
    if (len(sys.argv) != 3):
        print("Expected arg for directory for configs and arg for config file prefix")

    numConsensusRounds = 1000 # TODO We may want to change this for actual experiments
    numNodes = 10 # TODO may want to change this for actual experiments
    useCentralizedMultiArmedBandit = True
    possibleMValues = [1, 2, 3] # TODO We mayu want to change this for actual experiments
    sleepBetweenNodeProcessingMs = 0.1 # TODO May want to change this if it seems like we're sleeping too long. This is kind of arbitrary. This should be smaller than the average latency probably

    runConfig = RunConfig(numConsensusRounds, numNodes, possibleMValues, useCentralizedMultiArmedBandit, sleepBetweenNodeProcessingMs)

    roundsPerObservationPeriod = 10 # TODO we may want to change this for experiments. We want quite a few observation periods total, so if we increase this, we'll have to increase the number of rounds

    roundConfig = RoundConfig(roundsPerObservationPeriod)

    # TODO these are kind of arbitrary
    averageLatencyMs = 20
    latencyStdDevMs = 7
    maxLatencyMs = 50
    networkLatencyConfig = NetworkLatencyConfig(averageLatencyMs, latencyStdDevMs, maxLatencyMs)

    # TODO this should definitely change for final experiments
    # The first key should be 0 and the last key should be less than the total number of rounds
    # I think (need to think on this more) that the gap between keys (round to switch) should be greater than the observation period (ideally at least 3x greater -- need more rounds for this though)
    consensusRoundToSetMValue = {0: 3, 190: 2, 370:3, 510:1, 750:3}
    # consensusRoundToSetMValue = {0: 2, 19: 2, 37:2, 51:2, 75:2} # Constant
    percentDropMessage = 0.0 # TODO this is somewhat abitrary. Needs to be between 0 and 1. Having it too high just means using the default a lot, so that's probably not what we want
    defaultConsensusValue = True

    byzantineErrorConfig = ByzantineErrorConfig(consensusRoundToSetMValue, percentDropMessage, defaultConsensusValue)

    minMValueMargin = 1 # If we increase the number of nodes, this should probably increase
    decentralizedMultiArmedBanditFaultToleranceValue = math.floor((numNodes - 1)/3)

    # This is also arbitrary. Constraints are that the minMvalueMargin is satisfied and the two values are a subset of the possible m values
    defaultMValuePair = [possibleMValues[-2], possibleMValues[-1]]
    distributedMABConfig = DistributedMABConfig(minMValueMargin, decentralizedMultiArmedBanditFaultToleranceValue, defaultMValuePair)

    multiArmedBanditConfig = MultiArmedBanditConfig() # TODO Sai, I left this in case the multi-armed bandit piece needs parameters. Nothing needed for now

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
        RUN_CONFIG_FILE_YAML_NAME : runConfigFileName,
        MULTI_ARMED_BANDIT_CONFIG_FILE_YAML_NAME : multiArmedBanditConfigFileName,
        ROUND_CONFIG_FILE_YAML_NAME : roundConfigFileName,
        NETWORK_LATENCY_CONFIG_FILE_YAML_NAME : networkLatencyConfigFileName,
        BYZANTINE_ERROR_CONFIG_FILE_YAML_NAME : byzantineErrorConfigFileName,
        DISTRIBUTED_MAB_CONFIG_FILE_YAML_NAME : distributedMABConfigFileName
    }

    # TODO verify that this is right
    with open(yamlFileName, 'w') as outfile:
        yaml.dump(yamlOutData, outfile)







