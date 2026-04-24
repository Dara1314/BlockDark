#!/usr/bin/env python3
"""
==================================================================
🛡️ DDOS BLOCK DARK - VERSION 3.0 (PRO)
Founder: Dara Dav (imDara)
License: Open Source for Developers
==================================================================
"""

import socket
import threading
import time
import json
import os
import sys
import logging
import subprocess
import platform
from datetime import datetime, timedelta
from collections import defaultdict

# --- Auto Install Dependencies ---
try:
    from flask import Flask, request, jsonify, render_template_string
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    print("📦 Installing Flask and dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
    from flask import Flask, request, jsonify, render_template_string
    from flask_cors import CORS
    FLASK_AVAILABLE = True

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('ddos_block_dark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DDoS_Block_Dark")

class DDoSBlockDark:
    """Main DDoS Protection Engine"""
    
    def __init__(self):
        # Core data structures
        self.blocked_ips = set()
        self.whitelisted_ips = {'127.0.0.1', 'localhost', '::1'}
        self.temp_blocked = {}
        self.request_tracker = defaultdict(list)
        self.attack_logs = []
        self.running = True
        
        # Protection thresholds
        self.rate_limit_per_minute = 100
        self.burst_limit_per_second = 20
        self.temp_block_duration = 300
        self.ddos_threshold = 500
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'blocked_total': 0,
            'ddos_attacks': 0,
            'botnets_detected': 0,
            'start_time': time.time()
        }
        
        # Botnet tracking
        self.botnet_tracker = defaultdict(lambda: {
            'count': 0,
            'first_seen': time.time(),
            'last_seen': time.time(),
            'pattern_score': 0
        })
        
        # Load saved data
        self.load_data()
        
        # Start background services
        self.start_background_services()
        
        logger.info("✅ DDoS Block Dark v3.0 Initialized Successfully")
        self.print_banner()
    
    def print_banner(self):
        """Display cool banner"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗ ██████╗  ██████╗ ███████╗    ██████╗ ██╗              ║
║   ██╔══██╗██╔══██╗██╔═══██╗██╔════╝    ██╔══██╗██║              ║
║   ██║  ██║██████╔╝██║   ██║███████╗    ██████╔╝██║              ║
║   ██║  ██║██╔══██╗██║   ██║╚════██║    ██╔══██╗██║              ║
║   ██████╔╝██████╔╝╚██████╔╝███████║    ██████╔╝███████╗         ║
║   ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝    ╚═════╝ ╚══════╝         ║
║                                                                  ║
║         Advanced DDoS Protection & Botnet Defense System        ║
║                    Founder: Dara Dav (imDara)                    ║
║                         Version: 3.0                             ║
╚══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"\n{'='*60}")
        print(f"🔒 System Status: 🟢 ACTIVE")
        print(f"📊 Protection Mode: FULL DEFENSE")
        print(f"🎯 Rate Limit: {self.rate_limit_per_minute} req/min")
        print(f"🎯 Burst Limit: {self.burst_limit_per_second} req/sec")
        print(f"🎯 DDoS Threshold: {self.ddos_threshold} requests")
        print(f"{'='*60}\n")
    
    def load_data(self):
        """Load persistent data from files"""
        try:
            if os.path.exists('blocked_ips.json'):
                with open('blocked_ips.json', 'r') as f:
                    data = json.load(f)
                    self.blocked_ips = set(data) if isinstance(data, list) else set(data.keys())
                logger.info(f"📁 Loaded {len(self.blocked_ips)} blocked IPs")
            
            if os.path.exists('whitelist.json'):
                with open('whitelist.json', 'r') as f:
                    data = json.load(f)
                    self.whitelisted_ips.update(data)
                logger.info(f"✓ Loaded {len(self.whitelisted_ips)} whitelisted IPs")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def save_data(self):
        """Save persistent data to files"""
        try:
            with open('blocked_ips.json', 'w') as f:
                json.dump(list(self.blocked_ips), f, indent=2)
            with open('whitelist.json', 'w') as f:
                json.dump(list(self.whitelisted_ips), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def add_firewall_rule(self, ip):
        """Add system firewall rule to block IP"""
        try:
            system = platform.system().lower()
            if system == "windows":
                cmd = f'netsh advfirewall firewall add rule name="DDoS_Block_{ip}" dir=in action=block remoteip={ip}'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            elif system == "linux":
                subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], capture_output=True, timeout=5)
            logger.debug(f"Firewall rule added for {ip}")
        except Exception as e:
            logger.debug(f"Could not add firewall rule: {e}")
    
    def remove_firewall_rule(self, ip):
        """Remove system firewall rule"""
        try:
            system = platform.system().lower()
            if system == "windows":
                cmd = f'netsh advfirewall firewall delete rule name="DDoS_Block_{ip}"'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            elif system == "linux":
                subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], capture_output=True, timeout=5)
        except Exception as e:
            logger.debug(f"Could not remove firewall rule: {e}")
    
    def block_ip(self, ip, reason="Policy violation", permanent=True):
        """Block an IP address"""
        if ip in self.whitelisted_ips:
            return False
        
        if permanent:
            if ip not in self.blocked_ips:
                self.blocked_ips.add(ip)
                self.stats['blocked_total'] += 1
                logger.warning(f"🔒 PERMANENT BLOCK: {ip} | Reason: {reason}")
                self.add_firewall_rule(ip)
        else:
            self.temp_blocked[ip] = time.time() + self.temp_block_duration
            logger.warning(f"⏰ TEMP BLOCK: {ip} | Duration: {self.temp_block_duration}s | Reason: {reason}")
        
        # Log attack
        self.attack_logs.append({
            'timestamp': datetime.now().isoformat(),
            'ip': ip,
            'reason': reason,
            'type': 'ddos' if 'DDoS' in reason or 'Burst' in reason else 'rate_limit'
        })
        
        if 'Burst' in reason or 'DDoS' in reason:
            self.stats['ddos_attacks'] += 1
        
        self.save_data()
        return True
    
    def unblock_ip(self, ip):
        """Unblock an IP address"""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            self.remove_firewall_rule(ip)
            logger.info(f"🔓 UNBLOCKED: {ip}")
        if ip in self.temp_blocked:
            del self.temp_blocked[ip]
        self.save_data()
        return True
    
    def add_whitelist(self, ip):
        """Add IP to whitelist"""
        self.whitelisted_ips.add(ip)
        if ip in self.blocked_ips:
            self.unblock_ip(ip)
        if ip in self.temp_blocked:
            del self.temp_blocked[ip]
        self.save_data()
        logger.info(f"✓ Added {ip} to whitelist")
        return True
    
    def check_traffic(self, ip):
        """Validate and check traffic for DDoS patterns"""
        now = time.time()
        
        # Check if already blocked
        if ip in self.blocked_ips:
            return False
        
        # Check temporary block
        if ip in self.temp_blocked:
            if now < self.temp_blocked[ip]:
                return False
            else:
                del self.temp_blocked[ip]
        
        # Clean old request records
        self.request_tracker[ip] = [t for t in self.request_tracker[ip] if now - t < 60]
        
        # Check rate limit per minute
        minute_requests = len(self.request_tracker[ip])
        if minute_requests >= self.rate_limit_per_minute:
            self.block_ip(ip, f"Rate limit exceeded: {minute_requests} req/min", permanent=False)
            return False
        
        # Check burst limit per second
        second_requests = len([t for t in self.request_tracker[ip] if now - t < 1])
        if second_requests >= self.burst_limit_per_second:
            self.block_ip(ip, f"DDoS Burst Attack: {second_requests} req/sec", permanent=True)
            return False
        
        # Track request
        self.request_tracker[ip].append(now)
        self.stats['total_requests'] += 1
        
        # Check for botnet patterns
        self.detect_botnet(ip)
        
        return True
    
    def detect_botnet(self, ip):
        """Detect botnet attack patterns"""
        tracker = self.botnet_tracker[ip]
        now = time.time()
        
        tracker['count'] += 1
        tracker['last_seen'] = now
        
        # Calculate request rate
        time_span = now - tracker['first_seen']
        if time_span > 0:
            rate = tracker['count'] / time_span
            
            # Calculate pattern score
            pattern_score = 0
            if rate > 10:
                pattern_score += 20
            if tracker['count'] > self.ddos_threshold:
                pattern_score += 30
            if len(self.request_tracker[ip]) > 50:
                pattern_score += 20
            
            tracker['pattern_score'] = pattern_score
            
            # Block if pattern score is high
            if pattern_score > 40:
                self.stats['botnets_detected'] += 1
                self.block_ip(ip, f"Botnet DDoS Detected - Score: {pattern_score}", permanent=True)
                return True
        
        # Reset tracker every hour
        if time_span > 3600:
            del self.botnet_tracker[ip]
        
        return False
    
    def start_background_services(self):
        """Start background cleanup and monitoring services"""
        
        def cleanup_worker():
            """Clean old request data every minute"""
            while self.running:
                time.sleep(60)
                now = time.time()
                
                # Clean request tracker
                for ip in list(self.request_tracker.keys()):
                    self.request_tracker[ip] = [t for t in self.request_tracker[ip] if now - t < 300]
                    if not self.request_tracker[ip]:
                        del self.request_tracker[ip]
                
                # Clean temporary blocks
                for ip in list(self.temp_blocked.keys()):
                    if now > self.temp_blocked[ip]:
                        del self.temp_blocked[ip]
        
        def auto_report_worker():
            """Generate auto reports every 10 minutes"""
            while self.running:
                time.sleep(600)
                if len(self.blocked_ips) > 5:
                    self.generate_report()
        
        threading.Thread(target=cleanup_worker, daemon=True).start()
        threading.Thread(target=auto_report_worker, daemon=True).start()
    
    def generate_report(self):
        """Generate threat report"""
        uptime = time.time() - self.stats['start_time']
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(timedelta(seconds=int(uptime))),
            'statistics': self.stats,
            'blocked_ips': list(self.blocked_ips),
            'temp_blocked': list(self.temp_blocked.keys()),
            'recent_attacks': self.attack_logs[-20:],
            'configuration': {
                'rate_limit_per_minute': self.rate_limit_per_minute,
                'burst_limit_per_second': self.burst_limit_per_second,
                'ddos_threshold': self.ddos_threshold
            }
        }
        
        filename = f"ddos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report saved: {filename}")
        return filename
    
    def get_stats(self):
        """Get current statistics"""
        uptime = time.time() - self.stats['start_time']
        return {
            'status': '🟢 PROTECTING' if self.running else '🔴 STOPPED',
            'uptime': str(timedelta(seconds=int(uptime))),
            'total_requests': self.stats['total_requests'],
            'blocked_total': self.stats['blocked_total'],
            'currently_blocked': len(self.blocked_ips),
            'temp_blocked': len(self.temp_blocked),
            'ddos_attacks': self.stats['ddos_attacks'],
            'botnets_detected': self.stats['botnets_detected'],
            'whitelisted': len(self.whitelisted_ips),
            'active_monitoring': len(self.request_tracker)
        }

# --- Flask Web Dashboard ---
engine = DDoSBlockDark()
app = Flask(__name__)
CORS(app)

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DDoS Block Dark - Protection Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            font-family: 'Courier New', 'Segoe UI', monospace;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .glass {
            background: rgba(10, 10, 20, 0.7);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(0, 242, 255, 0.3);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .header {
            text-align: center;
            border-bottom: 2px solid #00f2ff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 48px;
            letter-spacing: 5px;
            background: linear-gradient(135deg, #00f2ff, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 15px;
            background: #00ff88;
            color: #0a0a0f;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(0, 242, 255, 0.05);
            border: 1px solid rgba(0, 242, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0, 242, 255, 0.2);
        }
        
        .stat-title {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #00f2ff;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: white;
        }
        
        .section-title {
            font-size: 24px;
            margin-bottom: 20px;
            color: #00f2ff;
            border-left: 4px solid #00f2ff;
            padding-left: 15px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th {
            text-align: left;
            padding: 15px;
            background: rgba(0, 242, 255, 0.1);
            color: #00f2ff;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(0, 242, 255, 0.1);
            color: #ccc;
        }
        
        .blocked-ip {
            color: #ff4757;
            font-family: monospace;
            font-weight: bold;
        }
        
        .btn {
            background: linear-gradient(135deg, #ff4757, #c0392b);
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px #ff4757;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #00b894, #009432);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #00f2ff, #0066ff);
        }
        
        .control-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .control-group {
            background: rgba(0, 242, 255, 0.03);
            padding: 20px;
            border-radius: 15px;
        }
        
        .control-group input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(0, 242, 255, 0.3);
            border-radius: 5px;
            color: white;
            font-family: monospace;
        }
        
        .control-group input:focus {
            outline: none;
            border-color: #00f2ff;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .alert {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass">
            <div class="header">
                <h1>🛡️ DDOS BLOCK DARK</h1>
                <p>Advanced DDoS Protection & Botnet Defense System</p>
                <div>
                    <span class="badge" id="statusBadge">● PROTECTING</span>
                    <span style="margin-left: 15px;">Founder: <strong>Dara Dav (imDara)</strong></span>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">TOTAL REQUESTS</div>
                    <div class="stat-value" id="totalRequests">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">BLOCKED IPS</div>
                    <div class="stat-value" id="blockedCount">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">DDoS ATTACKS</div>
                    <div class="stat-value" id="ddosAttacks">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">BOTNETS</div>
                    <div class="stat-value" id="botnets">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">UPTIME</div>
                    <div class="stat-value" id="uptime">0h</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">TEMP BLOCKED</div>
                    <div class="stat-value" id="tempBlocked">0</div>
                </div>
            </div>
            
            <div class="glass">
                <div class="section-title">🔒 BLOCKED IP REGISTRY</div>
                <table>
                    <thead>
                        <tr><th>IP ADDRESS</th><th>STATUS</th><th>ACTION</th></tr>
                    </thead>
                    <tbody id="blockedTableBody">
                        <tr><td colspan="3">Loading......</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="glass">
                <div class="section-title">⚙️ CONTROL PANEL</div>
                <div class="control-panel">
                    <div class="control-group">
                        <h3>🔨 Block IP</h3>
                        <input type="text" id="blockIpInput" placeholder="Enter IP address">
                        <button class="btn" onclick="blockIP()">BLOCK IP</button>
                    </div>
                    <div class="control-group">
                        <h3>🔓 Unblock IP</h3>
                        <input type="text" id="unblockIpInput" placeholder="Enter IP address">
                        <button class="btn btn-success" onclick="unblockIP()">UNBLOCK IP</button>
                    </div>
                    <div class="control-group">
                        <h3>✓ Whitelist IP</h3>
                        <input type="text" id="whitelistInput" placeholder="Enter IP address">
                        <button class="btn btn-primary" onclick="addWhitelist()">ADD TO WHITELIST</button>
                    </div>
                    <div class="control-group">
                        <h3>📊 Reports</h3>
                        <button class="btn btn-success" onclick="generateReport()">GENERATE REPORT</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('totalRequests').innerText = data.total_requests || 0;
                document.getElementById('blockedCount').innerText = data.currently_blocked || 0;
                document.getElementById('ddosAttacks').innerText = data.ddos_attacks || 0;
                document.getElementById('botnets').innerText = data.botnets_detected || 0;
                document.getElementById('uptime').innerText = data.uptime || '0h';
                document.getElementById('tempBlocked').innerText = data.temp_blocked || 0;
                
                const blockedResponse = await fetch('/api/blocked');
                const blockedData = await blockedResponse.json();
                
                const tbody = document.getElementById('blockedTableBody');
                if (blockedData.blocked && blockedData.blocked.length > 0) {
                    tbody.innerHTML = blockedData.blocked.map(ip => `
                        <tr>
                            <td class="blocked-ip">${ip}</td>
                            <td><span style="color: #ff4757;">● PERMANENT BLOCK</span></td>
                            <td><button class="btn-success" onclick="unblockSpecificIP('${ip}')">UNBLOCK</button></td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="3">✅ No blocked IPs</td></tr>';
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function blockIP() {
            const ip = document.getElementById('blockIpInput').value;
            if (!ip) {
                alert('Please enter an IP address');
                return;
            }
            
            try {
                const response = await fetch('/api/block', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: ip})
                });
                const result = await response.json();
                if (result.success) {
                    alert(`✅ ${result.message}`);
                    document.getElementById('blockIpInput').value = '';
                    refreshData();
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        async function unblockIP() {
            const ip = document.getElementById('unblockIpInput').value;
            if (!ip) {
                alert('Please enter an IP address');
                return;
            }
            unblockSpecificIP(ip);
        }
        
        async function unblockSpecificIP(ip) {
            try {
                const response = await fetch('/api/unblock', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: ip})
                });
                const result = await response.json();
                if (result.success) {
                    alert(`✅ ${result.message}`);
                    document.getElementById('unblockIpInput').value = '';
                    refreshData();
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        async function addWhitelist() {
            const ip = document.getElementById('whitelistInput').value;
            if (!ip) {
                alert('Please enter an IP address');
                return;
            }
            
            try {
                const response = await fetch('/api/whitelist/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: ip})
                });
                const result = await response.json();
                if (result.success) {
                    alert(`✅ ${result.message}`);
                    document.getElementById('whitelistInput').value = '';
                    refreshData();
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        async function generateReport() {
            try {
                const response = await fetch('/api/report', {method: 'POST'});
                const result = await response.json();
                if (result.success) {
                    alert(`✅ Threat report generated!\n📁 File: ${result.file}`);
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        setInterval(refreshData, 3000);
        refreshData();
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    return jsonify(engine.get_stats())

@app.route('/api/blocked')
def api_blocked():
    return jsonify({
        'blocked': list(engine.blocked_ips),
        'temp_blocked': list(engine.temp_blocked.keys()),
        'whitelisted': list(engine.whitelisted_ips)
    })

@app.route('/api/block', methods=['POST'])
def api_block():
    ip = request.json.get('ip')
    if ip:
        engine.block_ip(ip, "Manual admin block", permanent=True)
        return jsonify({'success': True, 'message': f'Blocked {ip}'})
    return jsonify({'success': False, 'message': 'No IP provided'})

@app.route('/api/unblock', methods=['POST'])
def api_unblock():
    ip = request.json.get('ip')
    if ip:
        engine.unblock_ip(ip)
        return jsonify({'success': True, 'message': f'Unblocked {ip}'})
    return jsonify({'success': False, 'message': 'No IP provided'})

@app.route('/api/whitelist/add', methods=['POST'])
def api_add_whitelist():
    ip = request.json.get('ip')
    if ip:
        engine.add_whitelist(ip)
        return jsonify({'success': True, 'message': f'Added {ip} to whitelist'})
    return jsonify({'success': False, 'message': 'No IP provided'})

@app.route('/api/report', methods=['POST'])
def api_report():
    filename = engine.generate_report()
    return jsonify({'success': True, 'file': filename, 'message': 'Report generated successfully'})

# --- Protection Server on Port 8888 ---
def start_protection_server():
    """Start TCP protection server for DDoS mitigation"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', 8888))
        server.listen(1000)
        logger.info("🛡️ Protection Node Active on Port 8888")
        logger.info("🌐 Listening for incoming connections...")
        
        while True:
            try:
                client, addr = server.accept()
                ip = addr[0]
                
                if engine.check_traffic(ip):
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n✅ Connection secured by DDoS Block Dark\r\n"
                    client.send(response.encode())
                client.close()
            except Exception as e:
                logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"Failed to start protection server: {e}")
    finally:
        server.close()

# --- Main Entry Point ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 STARTING DDOS BLOCK DARK v3.0")
    print("="*60)
    print(f"📊 Web Dashboard: http://localhost:5000")
    print(f"🛡️ Protection Port: 8888")
    print(f"👤 Founder: Dara Dav (imDara)")
    print("="*60 + "\n")
    
    # Start protection server in background
    protection_thread = threading.Thread(target=start_protection_server, daemon=True)
    protection_thread.start()
    
    # Start Flask web server
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down DDoS Block Dark...")
        engine.running = False
        sys.exit(0)
