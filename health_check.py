# -*- coding: utf-8 -*-
"""
Health check endpoint para Railway monitorizar o bot
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Estado global do bot
bot_status = {
    'healthy': True,
    'last_update': datetime.now().isoformat(),
    'conflicts': 0,
    'errors': 0
}


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health check HTTP"""
    
    def do_GET(self):
        """Responder a GET requests"""
        if self.path == '/health':
            # Atualizar timestamp
            bot_status['last_update'] = datetime.now().isoformat()
            
            # Responder com status
            self.send_response(200 if bot_status['healthy'] else 503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(bot_status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suprimir logs HTTP desnecessários"""
        pass


def start_health_check_server(port=8080):
    """Iniciar servidor de health check em thread separada"""
    def run_server():
        try:
            server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
            logger.info(f"✅ Health check server iniciado na porta {port}")
            server.serve_forever()
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar health check server: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()


def update_bot_status(healthy=True, conflict=False, error=False):
    """Atualizar status do bot"""
    global bot_status
    bot_status['healthy'] = healthy
    bot_status['last_update'] = datetime.now().isoformat()
    
    if conflict:
        bot_status['conflicts'] += 1
    if error:
        bot_status['errors'] += 1
