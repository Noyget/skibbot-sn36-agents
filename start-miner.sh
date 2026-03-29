#!/bin/bash
# Standalone startup script for SN36 miner
# This allows PM2 to run it directly without bash wrapper

cd /home/openclaw/bittensor-workspace/autoppia-official
exec python3 -m agents.server
