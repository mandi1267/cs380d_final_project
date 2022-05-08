import sys
import joblib
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Need arguments: results file name, config file name.")
    
    res_fname = sys.argv[1]
    
    res = joblib.load(res_fname)

    # TODO: Load this from file
    roundsPerObservationPeriod = 10
    numConsensusRounds = 1000
    
    numObservationPeriods = numConsensusRounds // roundsPerObservationPeriod

    # for i, round_res in enumerate(res.perRoundResults):
    #     print('Round', i, round_res.latenciesByNode)
    
    # consensuses_by_node = []
    round_latencies = [round_res.latenciesByNode for round_res in res.perRoundResults]
    # for lats in round_latencies:
    #     print([v for k, v in (list(lats.items())[0][1]).items()])
    max_round_latencies = [max([v for k, v in (list(lats.items())[0][1]).items()]) for lats in round_latencies]

    obs_period_lats = [np.average(max_round_latencies[i*roundsPerObservationPeriod:(i+1)*roundsPerObservationPeriod]) for i in range(numObservationPeriods)]

    plt.plot(obs_period_lats, '-x')
    plt.title('Observation Period Latencies')
    plt.xlabel('Observation Period')
    plt.ylabel('Latency (ms)')
    
    plt.show()
