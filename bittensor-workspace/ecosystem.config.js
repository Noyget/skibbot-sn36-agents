module.exports = {
  apps: [
    {
      name: 'skibbot-miner',
      script: '/home/openclaw/.openclaw/workspace/bittensor-workspace/autoppia-official/neurons/miner.py',
      interpreter: 'python3',
      cwd: __dirname,
      args: '--netuid 36 --subtensor.network finney --wallet.name primary --wallet.hotkey miner --logging.debug --axon.port 8091',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      kill_timeout: 5000,  // Hard kill after 5 seconds if SIGTERM fails
      listen_timeout: 10000,  // Wait 10s for startup
      env: {
        PYTHONUNBUFFERED: '1',
        WALLET_NAME: 'primary',
        HOTKEY_NAME: 'miner',
        NETWORK: 'finney',
        NETUID: '36',
        AGENT_NAME: 'SkibBot Web Agents',
        GITHUB_URL: 'https://github.com/Noyget/skibbot-sn36-agents/commit/17bab7ca62dcdf909284dee9f1425004766c9df8',
        AXON_PORT: '8091',
      },
      error_file: '~/.pm2/logs/skibbot-miner-error.log',
      out_file: '~/.pm2/logs/skibbot-miner-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    }
  ],
  deploy: {
    production: {
      user: 'node',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'git@github.com:Noyget/skibbot-sn36-agents.git',
      path: '/home/openclaw/.openclaw/workspace/bittensor-workspace',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env production'
    }
  }
};
