import sys
from byzantine_mab_configs import *
from network_manager import *
from multiarmed_bandit_executor import *
import random
import joblib
from byzantine_mab_results import *


def getNextConsensusValue():
    """
    Get the next value that we want the nodes to agree upon. In the case of a loyal general, this will be what the
    generals sends out.

    :return: Next value that the nodes should agree upon.
    """
    return bool(random.getrandbits(1))


def getInitialFaultToleranceValue(possibleMValues, useCentralizedMab, minMValueMargin):
    """
    Get the initial fault tolerance value(s) to use. Number of faulty nodes that the consensus algorithm should
    tolerate. In the centralized case, this returns one value. In the decentralized case, returns a tuple of 2 m values
    separateed at least by the minMValueMargin.

    :param possibleMValues:     M values that the multi-armed bandit approach can evaluate.
    :param useCentralizedMab:   True if we're using the centralized version, false if using the distributed version
                                (need 2 values).
    :param minMValueMargin:     Minimum difference between the m values returned in the distributed case. Ignored in
                                the centralized case.

    :return: Initial m value(s) that the consensus algorithm should use. Single value in the centralized case, tuple of
    2 values in the decentralized case.
    """

    # TODO do we just want random or do we want to choose the most conservative to start?
    # Maybe this should be part of the multi-armed bandit decider instead
    if (useCentralizedMab):
        return random.choice(possibleMValues)
    else:
        # TODO need to choose 2 values
        pass


def runSimulation(superConfig):
    """
    Run the simulation and get results.

    :param superConfig: SuperConfig object that provides access to all configuration parameters

    :return: Results (FullResults) for the experiment
    """

    # Get the configurations
    runConfig = superConfig.getRoundConfig()
    byzantineErrorConfig = superConfig.getByzantineErrorConfig()
    roundConfig = superConfig.getRoundConfig()
    distributedMABConfig = superConfig.getDistributedMABConfig()
    multiArmedBanditConfig = superConfig.getMultiArmedBanditConfig()
    networkLatencyConfig = superConfig.getNetworkLatencyConfig()

    # Get the number of calls per round. Number of consensus rounds in each observation period. The fault tolerance
    # will be the same for each consensus round in the observation period.
    roundsPerObservationPeriod = roundConfig.roundsPerObservationPeriod

    # Initialize the full results
    fullResults = FullResults()

    consensusFaultToleranceValue = getInitialFaultToleranceValue(runConfig.possibleMValues,
                                                                 runConfig.useCentralizedMultiArmedBandit,
                                                                 distributedMABConfig.minMValueMargin)
    # Create nodes and make network
    networkManager = NetworkManager(networkLatencyConfig, runConfig.numNodes, byzantineErrorConfig.defaultValue,
                                    consensusFaultToleranceValue, byzantineErrorConfig.percentDropMessage,
                                    runConfig.useCentralizedMultiArmedBandit, runConfig.sleepBetweenNodeProcessingMs)

    # Get the number of consensus rounds to run for
    numConsensusRounds = runConfig.numConsensusRounds

    # Initialize the true number of faults to 0
    trueFaultsValue = 0

    # (Only used in the centralized case) Create the multi-armed bandit executor that will be used to decide the fault
    # tolerance of the consensus algorithm
    multiArmedBanditExecutor = MultiArmedBanditExecutor(runConfig.possibleMValues, multiArmedBanditConfig)

    # Run the experiments
    for i in range(numConsensusRounds):
        # Change the number of actual faulty nodes if the config says that a new faulty node count should be changed
        # in this round
        if (i in byzantineErrorConfig.consensusRoundToSetMValue.keys()):
            networkManager.changeNumFaultyNodes(byzantineErrorConfig.consensusRoundToSetMValue[i])

        # Set the nodes that should exhibit byzantine error in the next consensus round
        networkManager.updateFaultyNodes()

        # Get the true consensus value that should be passed around
        trueConsensusValue = getNextConsensusValue()

        # Trigger the nodes to start a consensus round
        # Latencies is map of m-value to map of node # to latency experienced
        # Consensuses is map of m-value to map of node # to the decision reached
        # Wait for the nodes to reach consensus and then get the results
        latencies, consensuses, currentFaultyNodes = networkManager.startConsensusAndGetNodeLatenciesAndDecisions(
            trueConsensusValue)

        # Get the individual values reached by the nodes -- if they came to the same consensus, this should have only
        # 1 entry
        decisionsSet = {}
        for mVal, decisionsForM in consensuses.items():
            decisionsSetForM = []
            for nodeNum, decision in decisionsForM.items():
                if not (nodeNum in currentFaultyNodes):
                    decisionsForM.append(decision)
            decisionsSet[mVal] = set(decisionsSetForM)

        # We only care if consensus wasn't reached, rather than if the consensus was wrong (TODO I think...?)
        didFail = {m_val: (len(decisionsSet[m_val]) > 1) for m_val in decisionsSet.keys()}

        # Update the results with the data from the most recent round
        resultsForRound = SingleRoundResults(latencies, consensuses, trueConsensusValue, didFail)
        fullResults.addRoundResults(resultsForRound, trueFaultsValue, consensusFaultToleranceValue)

        # If we've run the specified number of consensus rounds in the observation period, choose new m value(s) and
        # switch to a new observation period
        if ((i + 1) % roundsPerObservationPeriod):
            resultsSinceLastDecision = fullResults.getAndResetResultsSinceLastDecision()

            if (runConfig.useCentralizedMultiArmedBandit):
                # If using a centralized controller, get the next value of m to use and update the nodes to use this
                # value
                consensusFaultToleranceValue = multiArmedBanditExecutor.getNextValueOfM(resultsSinceLastDecision)
                networkManager.setConsensusTolerance(consensusFaultToleranceValue)
            else:
                # If using a distributed method to decide the fault tolerance, trigger them to agree on new value of m
                consensusFaultToleranceValue = networkManager.haveDistributedNodesChooseNextMValues()

    networkManager.shutdown()

    return fullResults


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print "There must be one additional argument provided which is the name of a file containing pointers to all" \
              " needed configuration files"
    superConfigFile = sys.argv[1]
    resultsOutputFile = sys.argv[2]

    # Read the configuration parameters
    superConfig = readSuperConfigYaml(superConfigFile)

    # Run the simulation and get the results
    fullResults = runSimulation(superConfig)

    # Output the results to file
    joblib.dump(fullResults, resultsOutputFile)
