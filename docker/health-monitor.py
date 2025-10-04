#!/usr/bin/env python3
"""
MedMatch AI Health Monitor
Creative Docker MCP Gateway service for comprehensive system monitoring
"""

import os
import time
import requests
import psycopg2
import redis
import json
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter

# Prometheus metrics
health_status = Gauge('medmatch_service_health', 'Service health status', ['service'])
request_count = Counter('medmatch_health_checks_total', 'Total health checks', ['service', 'status'])
response_time = Gauge('medmatch_response_time_seconds', 'Service response time', ['service'])

class HealthMonitor:
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://backend:8000')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://frontend:3000')
        self.postgres_url = os.getenv('POSTGRES_URL', 'postgres://medmatch:secure_password_2024@postgres:5432/medmatch')
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 30))
        
    def check_backend(self):
        """Check backend API health"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/v1/health", timeout=10)
            response_time_val = time.time() - start_time
            
            if response.status_code == 200:
                health_status.labels(service='backend').set(1)
                request_count.labels(service='backend', status='success').inc()
                response_time.labels(service='backend').set(response_time_val)
                return True, f"Backend healthy ({response_time_val:.2f}s)"
            else:
                health_status.labels(service='backend').set(0)
                request_count.labels(service='backend', status='error').inc()
                return False, f"Backend returned {response.status_code}"
                
        except Exception as e:
            health_status.labels(service='backend').set(0)
            request_count.labels(service='backend', status='error').inc()
            return False, f"Backend error: {str(e)}"
    
    def check_frontend(self):
        """Check frontend health"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.frontend_url}/health", timeout=10)
            response_time_val = time.time() - start_time
            
            if response.status_code == 200:
                health_status.labels(service='frontend').set(1)
                request_count.labels(service='frontend', status='success').inc()
                response_time.labels(service='frontend').set(response_time_val)
                return True, f"Frontend healthy ({response_time_val:.2f}s)"
            else:
                health_status.labels(service='frontend').set(0)
                request_count.labels(service='frontend', status='error').inc()
                return False, f"Frontend returned {response.status_code}"
                
        except Exception as e:
            health_status.labels(service='frontend').set(0)
            request_count.labels(service='frontend', status='error').inc()
            return False, f"Frontend error: {str(e)}"
    
    def check_postgres(self):
        """Check PostgreSQL database health"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            response_time_val = time.time() - start_time
            
            health_status.labels(service='postgres').set(1)
            request_count.labels(service='postgres', status='success').inc()
            response_time.labels(service='postgres').set(response_time_val)
            return True, f"PostgreSQL healthy ({response_time_val:.2f}s)"
            
        except Exception as e:
            health_status.labels(service='postgres').set(0)
            request_count.labels(service='postgres', status='error').inc()
            return False, f"PostgreSQL error: {str(e)}"
    
    def check_redis(self):
        """Check Redis cache health"""
        try:
            start_time = time.time()
            r = redis.Redis.from_url(self.redis_url)
            r.ping()
            response_time_val = time.time() - start_time
            
            health_status.labels(service='redis').set(1)
            request_count.labels(service='redis', status='success').inc()
            response_time.labels(service='redis').set(response_time_val)
            return True, f"Redis healthy ({response_time_val:.2f}s)"
            
        except Exception as e:
            health_status.labels(service='redis').set(0)
            request_count.labels(service='redis', status='error').inc()
            return False, f"Redis error: {str(e)}"
    
    def run_health_checks(self):
        """Run all health checks"""
        timestamp = datetime.now().isoformat()
        results = {}
        
        # Check all services
        results['backend'] = self.check_backend()
        results['frontend'] = self.check_frontend()
        results['postgres'] = self.check_postgres()
        results['redis'] = self.check_redis()
        
        # Log results
        print(f"[{timestamp}] Health Check Results:")
        for service, (healthy, message) in results.items():
            status = "✅ HEALTHY" if healthy else "❌ UNHEALTHY"
            print(f"  {service}: {status} - {message}")
        
        # Overall system health
        all_healthy = all(healthy for healthy, _ in results.values())
        overall_status = "🟢 SYSTEM HEALTHY" if all_healthy else "🔴 SYSTEM ISSUES"
        print(f"  Overall: {overall_status}")
        print("-" * 60)
        
        return results
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        print("🏥 MedMatch AI Health Monitor Starting...")
        print(f"📊 Prometheus metrics server starting on port 8080")
        
        # Start Prometheus metrics server
        start_http_server(8080)
        
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print(f"🔍 Monitoring services:")
        print(f"  - Backend: {self.backend_url}")
        print(f"  - Frontend: {self.frontend_url}")
        print(f"  - PostgreSQL: {self.postgres_url.replace('password', '***')}")
        print(f"  - Redis: {self.redis_url}")
        print("=" * 60)
        
        while True:
            try:
                self.run_health_checks()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                print("\n🛑 Health monitor stopping...")
                break
            except Exception as e:
                print(f"❌ Monitor error: {str(e)}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = HealthMonitor()
    monitor.start_monitoring()