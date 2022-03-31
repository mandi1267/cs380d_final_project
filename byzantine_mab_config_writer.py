import joblib
import os
import sys
from byzantine_mab_configs import *
import yaml

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
        print "Expected arg for directory for configs and arg for config file prefix"

    # TODO create configs and set values
    runConfig = None
    multiArmedBanditConfig = None
    roundConfig = None
    networkLatencyConfig = None
    byzantineErrorConfig = None
    distributedMABConfig = None

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







