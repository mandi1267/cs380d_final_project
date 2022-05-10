import sys
import joblib
import matplotlib.pyplot as plt
import numpy as np
import statistics
from byzantine_mab_results import *
from byzantine_mab_configs import *
from collections import defaultdict


def getAverageLatencyOverObsPeriodForEachRound(latencies, observationPeriodStarts):
    numRounds = len(latencies)

    effectiveObservationPeriodStarts = []
    if observationPeriodStarts[0] > 0:
        effectiveObservationPeriodStarts.append(0)
        effectiveObservationPeriodStarts.extend(observationPeriodStarts)
    else:
        effectiveObservationPeriodStarts = observationPeriodStarts[:]

    aggregateLatencyForObsPeriod = []
    latenciesForObservationPeriod = []
    latencyCountInObsPeriod = []
    nextObsPeriodIdx = 1
    for i in range(numRounds):
        if nextObsPeriodIdx < len(effectiveObservationPeriodStarts):
            nextObsPeriodStart = effectiveObservationPeriodStarts[nextObsPeriodIdx]
            if i >= nextObsPeriodStart:
                nextObsPeriodIdx += 1
        currObsPeriodIdx = nextObsPeriodIdx - 1
        if (currObsPeriodIdx >= len(aggregateLatencyForObsPeriod)):
            aggregateLatencyForObsPeriod.append(0)
            latencyCountInObsPeriod.append(0)
            latenciesForObservationPeriod.append([])

        latenciesForRound = latencies[i]
        latenciesForObservationPeriod[currObsPeriodIdx].extend(latenciesForRound)
        for latency in latenciesForRound:
            aggregateLatencyForObsPeriod[currObsPeriodIdx] += latency
            latencyCountInObsPeriod[currObsPeriodIdx] += 1

    avgLatencyForObsPeriod = []
    stdDevForObsPeriod = []
    for obsPeriodIdx in range(len(aggregateLatencyForObsPeriod)):
        avgLatencyForObsPeriod.append(aggregateLatencyForObsPeriod[obsPeriodIdx] / latencyCountInObsPeriod[obsPeriodIdx])
        stdDevForObsPeriod.append(statistics.stdev(latenciesForObservationPeriod[obsPeriodIdx]))

    latenciesAvgOverObsPeriod = []
    stdDevsByRoundOverObsPeriod = []
    nextObsPeriodIdx = 1
    for i in range(numRounds):
        if nextObsPeriodIdx < len(effectiveObservationPeriodStarts):
            nextObsPeriodStart = effectiveObservationPeriodStarts[nextObsPeriodIdx]
            if i >= nextObsPeriodStart:
                nextObsPeriodIdx += 1
        currObsPeriodIdx = nextObsPeriodIdx - 1
        latenciesAvgOverObsPeriod.append(avgLatencyForObsPeriod[currObsPeriodIdx])
        stdDevsByRoundOverObsPeriod.append(stdDevForObsPeriod[currObsPeriodIdx])

    return np.array(latenciesAvgOverObsPeriod), np.array(stdDevsByRoundOverObsPeriod)


def plotLatencies(chosenMLatencies, observationPeriodFirstRound, conservativeMLatencies=None):
    """

    :param chosenMLatencies:                List of lists. Each inner list is the list of latencies experienced by the
                                            nodes for a particular round when using the multi-armed bandit to choose the
                                            m value. Includes the latency for the commanding node (which should be
                                            removed before plotting).
    :param observationPeriodFirstRound:     List of integers, where each integer indicates round in which an observation
                                            period started the start of an observation period.
    :param conservativeMLatencies:          Optional latencies for the most conservative m value for a given number of
                                            nodes. If provided, will have the same format as chosenMLatencies.
    :return:
    """

    numRounds = len(chosenMLatencies)

    xVals = np.array(range(numRounds))

    # for obsPeriodStart in observationPeriodFirstRound:
    #     plt.axvline(obsPeriodStart, alpha=0.2)

    chosenMLatenciesNoCommandingGeneral = []

    chosenMLatenciesAvgByRound = []
    chosenMLatenciesStdDevByRound = []
    chosenMLatenciesMinByRound = []
    chosenMLatenciesMaxByRound = []

    # Remove the time for the commanding general because it isn't impacted by the value of m
    for chosenMLatencyForRound in chosenMLatencies:
        chosenMLatencyForRoundNoCommandingGeneral = chosenMLatencyForRound[:]
        chosenMLatencyForRoundNoCommandingGeneral.remove(min(chosenMLatencyForRoundNoCommandingGeneral))
        chosenMLatenciesNoCommandingGeneral.append(chosenMLatencyForRoundNoCommandingGeneral)

        chosenMLatenciesAvgByRound.append(statistics.mean(chosenMLatencyForRoundNoCommandingGeneral))
        chosenMLatenciesStdDevByRound.append(statistics.stdev(chosenMLatencyForRoundNoCommandingGeneral))
        chosenMLatenciesMinByRound.append(min(chosenMLatencyForRoundNoCommandingGeneral))
        chosenMLatenciesMaxByRound.append(max(chosenMLatencyForRoundNoCommandingGeneral))

    chosenMLatenciesAvgByRoundNp = np.array(chosenMLatenciesAvgByRound)
    chosenMLatenciesStdDevByRoundNp = np.array(chosenMLatenciesStdDevByRound)
    chosenMLatenciesMinByRoundNp = np.array(chosenMLatenciesMinByRound)
    chosenMLatenciesMaxByRoundNp = np.array(chosenMLatenciesMaxByRound)

    # plt.plot(xVals, chosenMLatenciesAvgByRoundNp, color="b", label="MAB M Value", alpha=0.4)
    # plt.fill_between(xVals, chosenMLatenciesAvgByRoundNp - chosenMLatenciesStdDevByRoundNp,
    #                  chosenMLatenciesAvgByRoundNp + chosenMLatenciesStdDevByRoundNp, alpha=0.4, color="b")
    # plt.fill_between(xVals, chosenMLatenciesMinByRoundNp, chosenMLatenciesMaxByRoundNp, alpha=0.2, color="b")

    chosenMLatenciesAvgOverObsPeriod, chosenMLatenciesStdDevOverObsPeriod = getAverageLatencyOverObsPeriodForEachRound(chosenMLatencies,
                                                                                  observationPeriodFirstRound)

    plt.plot(xVals, chosenMLatenciesAvgOverObsPeriod, color="b", label="MAB (Average)")

    plt.fill_between(xVals, chosenMLatenciesAvgOverObsPeriod - chosenMLatenciesStdDevOverObsPeriod,
                     chosenMLatenciesAvgOverObsPeriod + chosenMLatenciesStdDevOverObsPeriod, alpha=0.2, color="b", label="MAB (+/- std dev)")

    plt.title("Latency by Observation Periods")
    plt.xlabel("Round Number")
    plt.ylabel("Latency (ms)")
    plt.xlim(0, numConsensusRounds)
    plt.ylim(bottom=0)


    if (conservativeMLatencies):
        conservativeMLatenciesNoCommandingGeneral = []

        conservativeMLatenciesAvgByRound = []
        conservativeMLatenciesStdDevByRound = []
        conservativeMLatenciesMinByRound = []
        conservativeMLatenciesMaxByRound = []

        # Remove the time for the commanding general because it isn't impacted by the value of m
        for conservativeMLatencyForRound in conservativeMLatencies:
            conservativeMLatencyForRoundNoCommandingGeneral = conservativeMLatencyForRound[:]
            conservativeMLatencyForRoundNoCommandingGeneral.remove(min(conservativeMLatencyForRoundNoCommandingGeneral))
            conservativeMLatenciesNoCommandingGeneral.append(conservativeMLatencyForRoundNoCommandingGeneral)

            conservativeMLatenciesAvgByRound.append(statistics.mean(conservativeMLatencyForRoundNoCommandingGeneral))
            conservativeMLatenciesStdDevByRound.append(
                statistics.stdev(conservativeMLatencyForRoundNoCommandingGeneral))
            conservativeMLatenciesMinByRound.append(min(conservativeMLatencyForRoundNoCommandingGeneral))
            conservativeMLatenciesMaxByRound.append(max(conservativeMLatencyForRoundNoCommandingGeneral))

        conservativeMLatenciesAvgByRoundNp = np.array(conservativeMLatenciesAvgByRound)
        conservativeMLatenciesStdDevByRoundNp = np.array(conservativeMLatenciesStdDevByRound)
        conservativeMLatenciesMinByRoundNp = np.array(conservativeMLatenciesMinByRound)
        conservativeMLatenciesMaxByRoundNp = np.array(conservativeMLatenciesMaxByRound)

        xVals = np.array(range(numRounds))

        conservativeMLatenciesAvgOverObsPeriod, conservativeMLatenciesStdDevOverObsPeriod = getAverageLatencyOverObsPeriodForEachRound(conservativeMLatencies,
                                                                                            observationPeriodFirstRound)

        # plt.plot(xVals, conservativeMLatenciesAvgByRound, color="r", label="Conservative M Value", alpha=0.4)
        plt.plot(xVals, conservativeMLatenciesAvgOverObsPeriod, color="r",
                 label="Conservative (Average)")

        plt.fill_between(xVals, conservativeMLatenciesAvgOverObsPeriod - conservativeMLatenciesStdDevOverObsPeriod,
                         conservativeMLatenciesAvgOverObsPeriod + conservativeMLatenciesStdDevOverObsPeriod, alpha=0.2, color="r",
                         label="Conservative (+/- std dev)")
        # plt.fill_between(xVals, conservativeMLatenciesAvgByRoundNp - conservativeMLatenciesStdDevByRoundNp,
        #                  conservativeMLatenciesAvgByRoundNp + conservativeMLatenciesStdDevByRoundNp, alpha=0.4,
        #                  color="r")
        # plt.fill_between(xVals, conservativeMLatenciesMinByRoundNp, conservativeMLatenciesMaxByRoundNp, alpha=0.2,
        #                  color="r")

        plt.legend()

        plt.figure()

        latencyDifferences = conservativeMLatenciesAvgByRoundNp - chosenMLatenciesAvgByRoundNp
        cumulativeLatencySavings = np.copy(latencyDifferences)
        for i in range(1, numRounds):
            cumulativeLatencySavings[i] = latencyDifferences[i] + cumulativeLatencySavings[i - 1]

        plt.title("Aggregated Latency Savings")
        plt.xlabel("Round Number")
        plt.ylabel("Cumulative Latency Savings (ms)")
        plt.plot(xVals, cumulativeLatencySavings)

        plt.xlim(0, numConsensusRounds - 1)
    else:
        plt.legend()

    # plt.show()


def plotChosenMValuesAgainstTrueFaultyNodes(trueFaultyNodesByRound, chosenMValuesByRound, observationPeriodStarts):
    numRounds = len(chosenMLatencies)

    xVals = np.array(range(numRounds))

    plt.plot(xVals, np.array(chosenMValuesByRound), label="MAB M Value", color="b", alpha=0.6)
    plt.plot(xVals, np.array(trueFaultyNodesByRound), label="True Faulty Nodes Count", color="g", linewidth=3)

    # for obsPeriodStart in observationPeriodStarts:
    #     plt.axvline(obsPeriodStart, alpha=0.2)

    plt.title("MAB M Value vs True Faulty Nodes Count")
    plt.xlabel("Round Number")
    plt.ylabel("M Value")
    plt.xlim(0, numRounds)
    plt.ylim(bottom=0)
    plt.legend()
    # plt.show()


def plotPercentFailuresPerObservationPeriod(didFailByRound, mValueByRound, observationPeriodStarts):
    numRounds = len(didFailByRound)

    xVals = np.array(range(numRounds))

    effectiveObservationPeriodStarts = []
    if observationPeriodStarts[0] > 0:
        effectiveObservationPeriodStarts.append(0)
        effectiveObservationPeriodStarts.extend(observationPeriodStarts)
    else:
        effectiveObservationPeriodStarts = observationPeriodStarts[:]

    failuresForObsPeriod = []
    successesForObsPeriod = []
    nextObsPeriodIdx = 1
    percentFailureForObsPeriod = []
    for i in range(numRounds):
        if nextObsPeriodIdx < len(effectiveObservationPeriodStarts):
            nextObsPeriodStart = effectiveObservationPeriodStarts[nextObsPeriodIdx]
            if i >= nextObsPeriodStart:
                nextObsPeriodIdx += 1
        currObsPeriodIdx = nextObsPeriodIdx - 1
        if (currObsPeriodIdx >= len(failuresForObsPeriod)):
            failuresForObsPeriod.append(0)

        if (currObsPeriodIdx >= len(successesForObsPeriod)):
            successesForObsPeriod.append(0)

        if (didFailByRound[i]):
            failuresForObsPeriod[currObsPeriodIdx] += 1
        else:
            successesForObsPeriod[currObsPeriodIdx] += 1

    for obsPeriodIdx in range(len(failuresForObsPeriod)):
        failuresCount = failuresForObsPeriod[obsPeriodIdx]
        successesCount = successesForObsPeriod[obsPeriodIdx]
        failureRate = 100 * failuresCount / (successesCount + failuresCount)
        percentFailureForObsPeriod.append(failureRate)

    obsPeriodFailure = []
    nextObsPeriodIdx = 1
    for i in range(numRounds):
        if nextObsPeriodIdx < len(effectiveObservationPeriodStarts):
            nextObsPeriodStart = effectiveObservationPeriodStarts[nextObsPeriodIdx]
            if i >= nextObsPeriodStart:
                nextObsPeriodIdx += 1
        currObsPeriodIdx = nextObsPeriodIdx - 1
        obsPeriodFailure.append(percentFailureForObsPeriod[currObsPeriodIdx])

    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Round Number")
    ax1.set_ylabel("Percent Failures In Observation Period", color='b')
    ax1.plot(xVals, np.array(obsPeriodFailure), color='b', label="Percent Failures")
    ax1.tick_params(axis='y', labelcolor='b')

    ax2 = ax1.twinx()

    ax2.set_ylabel("MAB M Value", color='r')
    ax2.plot(xVals, np.array(mValueByRound), color='r', alpha=0.4, label="MAB M Value")
    ax2.tick_params(axis='y', labelcolor='r')

    # fig.tight_layout()

    # for obsPeriodStart in observationPeriodStarts:
    #     plt.axvline(obsPeriodStart, alpha=0.2)

    plt.xlim(0, numRounds)
    plt.title("Percent Failures by Observation Period and MAB M Value")
    # plt.legend()
    # plt.show()


if __name__ == "__main__":
    if ((len(sys.argv) != 3) and (len(sys.argv) != 4)):
        print("Need arguments: results file name, config file name, optional conservative m results file name")

    res_fname = sys.argv[1]
    configFileName = sys.argv[2]

    conservativeResFileName = None
    conservativeResults = None
    if (len(sys.argv) == 4):
        conservativeResFileName = sys.argv[3]
        conservativeResults = joblib.load(conservativeResFileName)

    res = joblib.load(res_fname)

    superConfig = readSuperConfigYaml(configFileName)
    runConfig = superConfig.getRunConfig()
    mabConfig = superConfig.getMultiArmedBanditConfig()
    roundConfig = superConfig.getRoundConfig()
    networkLatencyConfig = superConfig.getNetworkLatencyConfig()
    byzantineErrorConfig = superConfig.getByzantineErrorConfig()

    numConsensusRounds = runConfig.numConsensusRounds
    roundsPerObservationPeriod = roundConfig.roundsPerObservationPeriod

    observationPeriodStarts = range(0, numConsensusRounds, roundsPerObservationPeriod)

    numObservationPeriods = numConsensusRounds // roundsPerObservationPeriod

    # for i, round_res in enumerate(res.perRoundResults):
    #     print('Round', i, round_res.latenciesByNode)

    # # consensuses_by_node = []
    # round_latencies = [round_res.latenciesByNode for round_res in res.perRoundResults]
    # max_round_latencies = [min([v for k, v in lats[1].items()]) for lats in round_latencies]
    #
    # obs_period_lats = [
    #     np.average(max_round_latencies[i * roundsPerObservationPeriod:(i + 1) * roundsPerObservationPeriod]) for i in
    #     range(numObservationPeriods)]
    #
    # plt.plot(obs_period_lats, '-x')
    # plt.title('Observation Period Latencies')
    # plt.xlabel('Observation Period')
    # plt.ylabel('Latency (ms)')
    #
    # plt.show()

    chosenMLatencies = []

    for singleRoundResult in res.perRoundResults:
        latenciesForRound = []
        latenciesByNodeByM = singleRoundResult.latenciesByNode
        if (len(latenciesByNodeByM) != 1):
            print("There should only be 1 m value in the results")
            exit(1)
        for mVal, latenciesForM in latenciesByNodeByM.items():
            for nodeNum, latencyForNode in latenciesForM.items():
                latenciesForRound.append(latencyForNode)
        chosenMLatencies.append(latenciesForRound)

    conservativeMLatencies = None

    if (conservativeResults != None):
        conservativeMLatencies = []
        for singleRoundResult in conservativeResults.perRoundResults:
            latenciesForRound = []
            latenciesByNodeByM = singleRoundResult.latenciesByNode
            if (len(latenciesByNodeByM) != 1):
                print("There should only be 1 m value in the results")
                exit(1)
            for mVal, latenciesForM in latenciesByNodeByM.items():
                for nodeNum, latencyForNode in latenciesForM.items():
                    latenciesForRound.append(latencyForNode)
            conservativeMLatencies.append(latenciesForRound)

    # Plot latency of adaptive system vs latency of conservative m value
    plotLatencies(chosenMLatencies, observationPeriodStarts, conservativeMLatencies)

    # trueMValues = res.trueFaultyNodesCount
    # print(trueMValues)

    trueMValues = []
    trueMValue = 0
    for i in range(len(res.perRoundResults)):
        if (i in byzantineErrorConfig.consensusRoundToSetMValue.keys()):
            trueMValue = byzantineErrorConfig.consensusRoundToSetMValue[i]
        trueMValues.append(trueMValue)

    selectedMValues = []
    for singleRoundResult in res.perRoundResults:
        mValForRound = None
        latenciesByNodeByM = singleRoundResult.latenciesByNode
        if (len(latenciesByNodeByM) != 1):
            print("There should only be 1 m value in the results")
            exit(1)
        for mVal in latenciesByNodeByM:
            mValForRound = mVal
        selectedMValues.append(mValForRound)

    # Plot true m values against selected m value
    plt.figure()
    plotChosenMValuesAgainstTrueFaultyNodes(trueMValues, selectedMValues, observationPeriodStarts)


    # Plot failures (maybe with time with different y axis?) TODO (how?)
    percentFailuresByMValue = {}

    failuresByMValue = defaultdict(int)
    successesByMValue = defaultdict(int)
    totalFailures = 0
    didFailByRound = []
    for singleRoundResult in res.perRoundResults:
        didFailByM = singleRoundResult.didFail
        if (len(didFailByM) != 1):
            print("There should only be 1 m value in the results")
            exit(1)
        didFail = None
        mVal = None
        for indivMVal, didFailForM in didFailByM.items():
            didFail = didFailForM
            mVal = indivMVal

        if (didFail):
            totalFailures += 1
            failuresByMValue[mVal] += 1
        else:
            successesByMValue[mVal] += 1
        didFailByRound.append(didFail)

    mValues = list(failuresByMValue.keys())
    mValues.extend(successesByMValue.keys())

    for mVal in set(mValues):
        numFailures = failuresByMValue[mVal]
        percentFailuresByMValue[mVal] = numFailures / (numFailures + successesByMValue[mVal])

    # Plot the percentage of failed consensus rounds per observation period along with the chosen m value
    # plt.figure()
    plotPercentFailuresPerObservationPeriod(didFailByRound, selectedMValues, observationPeriodStarts)

    # Compute % of time that m value is greater than true value of m (safe)

    numSafeMValues = 0

    for i in range(numConsensusRounds):
        trueM = trueMValues[i]
        selectedMValue = selectedMValues[i]
        if (selectedMValue >= trueM):
            numSafeMValues += 1

    percentSafeMValues = numSafeMValues / numConsensusRounds
    print("Percent of Consensus Rounds Where M was Sufficiently Conservative: " + str(percentSafeMValues))

    # TODO do we actually need this
    # TODO Number of observation periods to converge to ideal value -- can this be a CDF?

    plt.show()
