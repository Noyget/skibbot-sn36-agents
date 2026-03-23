module.exports = {
  apps: [
    {
      name: 'nova-mainnet-miner',
      script: './nova_ml_build/neurons/miner.py',
      interpreter: 'python3',
      cwd: '/home/openclaw/.openclaw/workspace',
      args: '',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '4G',
      env: {
        PYTHONUNBUFFERED: '1',
        NETWORK: 'mainnet',
        SUBNET_UID: '68',
        MINER_UID: '6',
        TARGET: 'HDAC6',
        GITHUB_URL: 'https://github.com/Noyget/nova-molecular-scout/commit/e2ffa86',
      },
      error_file: '~/.pm2/logs/nova-mainnet-miner-error.log',
      out_file: '~/.pm2/logs/nova-mainnet-miner-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    }
  ]
};
