module.exports = {
  apps: [
    {
      name: 'nova-mainnet-miner',
      script: './nova_ml_build/neurons/miner_psichic.py',
      interpreter: 'python3',
      cwd: '/home/openclaw/.openclaw/workspace',
      args: '',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '4G',
      kill_timeout: 5000,  // Hard kill after 5 seconds if SIGTERM fails
      listen_timeout: 10000,  // Wait 10s for startup
      env: {
        PYTHONUNBUFFERED: '1',
        NETWORK: 'mainnet',
        SUBNET_UID: '68',
        MINER_UID: '6',
        TARGET: 'HDAC6',
        GITHUB_URL: 'https://github.com/Noyget/skibbot-sn36-agents/commit/7dc38a8',
      },
      error_file: '~/.pm2/logs/nova-mainnet-miner-error.log',
      out_file: '~/.pm2/logs/nova-mainnet-miner-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    }
  ]
};
