#!/usr/bin/env python3
"""
NOVA SN68 Blueprint Miner Entry Point
Wraps neurons/miner.py for Blueprint validator requirements.
"""

import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and run the actual miner
from neurons.miner import NovaInfiniteSampler

if __name__ == "__main__":
    sampler = NovaInfiniteSampler()
    sampler.run()
