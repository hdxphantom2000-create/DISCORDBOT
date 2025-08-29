"""
Web monitoring interface for Discord Translation Bot
Provides a Flask-based dashboard to monitor bot statistics
"""

from flask import Flask, render_template_string, jsonify
import time
from datetime import datetime

# Global bot instance reference
bot_instance = None

def set_bot_instance(bot):
    """Set the bot instance for monitoring"""
    global bot_instance
    bot_instance = bot

def create_web_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # HTML template for the monitoring dashboard
    DASHBOARD_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Discord Translation Bot Monitor</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .card { border: none; box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075); }
            .status-running { color: #198754; }
            .status-stopped { color: #dc3545; }
            .metric-card { transition: transform 0.2s; }
            .metric-card:hover { transform: translateY(-2px); }
            .flag-list { max-height: 400px; overflow-y: auto; }
            .flag-item { display: inline-block; margin: 5px; padding: 5px 10px; background-color: #e9ecef; border-radius: 15px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <div class="row">
                <div class="col-12">
                    <h1 class="mb-4">
                        <i class="fas fa-robot"></i> Discord Translation Bot Monitor
                    </h1>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <i class="fas fa-power-off fa-2x mb-2" id="status-icon"></i>
                            <h5 class="card-title">Status</h5>
                            <p class="card-text" id="bot-status">Loading...</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <i class="fas fa-language fa-2x mb-2 text-primary"></i>
                            <h5 class="card-title">Übersetzungen</h5>
                            <p class="card-text" id="translations-count">0</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <i class="fas fa-exclamation-triangle fa-2x mb-2 text-warning"></i>
                            <h5 class="card-title">Fehler</h5>
                            <p class="card-text" id="errors-count">0</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <i class="fas fa-server fa-2x mb-2 text-info"></i>
                            <h5 class="card-title">Server</h5>
                            <p class="card-text" id="guilds-count">-</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle"></i> Bot Informationen</h5>
                        </div>
                        <div class="card-body">
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Benutzer:</strong></td>
                                    <td id="users-count">-</td>
                                </tr>
                                <tr>
                                    <td><strong>Latenz:</strong></td>
                                    <td id="latency">-</td>
                                </tr>
                                <tr>
                                    <td><strong>Letzte Aktualisierung:</strong></td>
                                    <td id="last-update">-</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-flag"></i> Unterstützte Sprachen</h5>
                        </div>
                        <div class="card-body flag-list" id="supported-flags">
                            Loading...
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-line"></i> Nutzungsstatistiken</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="statsChart" width="400" height="100"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            let translationsHistory = [];
            let errorsHistory = [];
            let timeLabels = [];
            let chart;
            
            function initChart() {
                const ctx = document.getElementById('statsChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timeLabels,
                        datasets: [{
                            label: 'Übersetzungen',
                            data: translationsHistory,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            tension: 0.1
                        }, {
                            label: 'Fehler',
                            data: errorsHistory,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function updateStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        // Update status
                        const statusElement = document.getElementById('bot-status');
                        const statusIcon = document.getElementById('status-icon');
                        
                        if (data.status === 'Running') {
                            statusElement.textContent = 'Online';
                            statusElement.className = 'card-text status-running';
                            statusIcon.className = 'fas fa-power-off fa-2x mb-2 status-running';
                        } else {
                            statusElement.textContent = 'Offline';
                            statusElement.className = 'card-text status-stopped';
                            statusIcon.className = 'fas fa-power-off fa-2x mb-2 status-stopped';
                        }
                        
                        // Update metrics
                        document.getElementById('translations-count').textContent = data.translations || 0;
                        document.getElementById('errors-count').textContent = data.errors || 0;
                        document.getElementById('guilds-count').textContent = data.guilds || '-';
                        document.getElementById('users-count').textContent = data.users || '-';
                        document.getElementById('latency').textContent = data.latency ? data.latency + ' ms' : '-';
                        document.getElementById('last-update').textContent = new Date().toLocaleString('de-DE');
                        
                        // Update chart data
                        const now = new Date().toLocaleTimeString('de-DE');
                        timeLabels.push(now);
                        translationsHistory.push(data.translations || 0);
                        errorsHistory.push(data.errors || 0);
                        
                        // Keep only last 20 data points
                        if (timeLabels.length > 20) {
                            timeLabels.shift();
                            translationsHistory.shift();
                            errorsHistory.shift();
                        }
                        
                        chart.update();
                    })
                    .catch(error => {
                        console.error('Error fetching stats:', error);
                    });
            }
            
            function loadSupportedFlags() {
                fetch('/api/flags')
                    .then(response => response.json())
                    .then(data => {
                        const flagsContainer = document.getElementById('supported-flags');
                        flagsContainer.innerHTML = '';
                        
                        Object.entries(data.flags).forEach(([flag, lang]) => {
                            const flagItem = document.createElement('span');
                            flagItem.className = 'flag-item';
                            flagItem.innerHTML = `${flag} ${lang.toUpperCase()}`;
                            flagsContainer.appendChild(flagItem);
                        });
                    })
                    .catch(error => {
                        console.error('Error loading flags:', error);
                        document.getElementById('supported-flags').innerHTML = 'Fehler beim Laden der Sprachen';
                    });
            }
            
            // Initialize page
            document.addEventListener('DOMContentLoaded', function() {
                initChart();
                loadSupportedFlags();
                updateStats();
                
                // Update stats every 5 seconds
                setInterval(updateStats, 5000);
            });
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        return render_template_string(DASHBOARD_TEMPLATE)
    
    @app.route('/api/stats')
    def api_stats():
        """API endpoint for bot statistics"""
        if bot_instance:
            stats = bot_instance.get_stats()
        else:
            stats = {
                'translations': 0,
                'errors': 0,
                'status': 'Stopped',
                'guilds': 0,
                'users': 0,
                'latency': 0
            }
        
        return jsonify(stats)
    
    @app.route('/api/flags')
    def api_flags():
        """API endpoint for supported flags and languages"""
        if bot_instance and hasattr(bot_instance, 'FLAG_LANG_MAP'):
            flags = bot_instance.FLAG_LANG_MAP
        else:
            flags = {}
        
        return jsonify({'flags': flags})
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'bot_connected': bot_instance is not None and hasattr(bot_instance, 'stats')
        })
    
    return app
