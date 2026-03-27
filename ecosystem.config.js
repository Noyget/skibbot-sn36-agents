module.exports = {
  apps: [{
    name: 'skibbot-miner',
    script: 'agents/server.py',
    interpreter: 'python3',
    instances: 1,
    // WATCHDOG COMPLETELY DISABLED - DO NOT RE-ENABLE
    watch: false,
    autorestart: false,
    max_restarts: 0,
    max_memory_restart: "2G",
    error_file: "/dev/null",
    out_file: "/dev/null",
    log_file: "/dev/null",
    env: {
      "NODE_ENV": "production"
    }
  }]
};
