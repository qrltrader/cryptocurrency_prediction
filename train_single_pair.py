"""Script to train an agent to operate into the market according to the pair

Example:
    python train_single_pair.py \
        --algo PPO \
        --symbol XRP \
        --to_symbol USDT \
        --histo day \
        --limit 180

Lucas Draichi 2019
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import gym
import os
import ray
from gym.spaces import Discrete, Box
from sklearn.preprocessing import normalize
from configs.vars import *
from configs.functions import init_data, get_datasets
from envs import SinglePairTradingEnv
from ray.tune import run_experiments, grid_search
from ray.tune.registry import register_env
from configs.vars import WALLET_FIRST_SYMBOL, WALLET_SECOND_SYMBOL

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='\n')
    parser.add_argument('--symbol', type=str, help='Choose coin to train')
    parser.add_argument('--to_symbol', type=str, help='Choose coin to train')
    parser.add_argument('--histo', type=str, help='Daily or hourly data')
    parser.add_argument('--limit', type=int, help='How many data points')
    parser.add_argument('--algo', type=str, help='Choose algorithm to train')
    FLAGS = parser.parse_args()
    _ = get_datasets(FLAGS.symbol, FLAGS.to_symbol, FLAGS.histo, FLAGS.limit)
    keys, symbols = init_data(FLAGS.symbol + FLAGS.to_symbol, 'train', FLAGS.limit, FLAGS.histo)
    register_env("SinglePairTrading-v0", lambda config: SinglePairTradingEnv(config))
    ray.init()
    run_experiments({
        "clipparam_{}_{}_{}_wallet-{}-{}".format(FLAGS.symbol + FLAGS.to_symbol, FLAGS.limit, FLAGS.histo, WALLET_FIRST_SYMBOL, WALLET_SECOND_SYMBOL): {
            "run": FLAGS.algo,
            "env": "SinglePairTrading-v0",
            "stop": {
                "timesteps_total": 1e6, #1e6 = 1M
            },
            "checkpoint_freq": 100,
            "checkpoint_at_end": True,
            "config": {
                "lr": grid_search([
                    1e-4
                    # 1e-6
                ]),
                "num_workers": 3,  # parallelism
                'observation_filter': 'MeanStdFilter',
                "vf_clip_param": 10000000.0,
                "env_config": {
                    'keys': keys,
                    'symbols': symbols,
                    'first_coin': FLAGS.symbol,
                    'second_coin': FLAGS.to_symbol
                },
            }
        }
    })