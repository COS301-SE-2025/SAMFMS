#!/usr/bin/env python3
"""
SAMFMS Service Health Monitor
Monitors the health of all services and validates routing configuration
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    def __init__(self):
        self.services = {
            'core': {'url': 'http://localhost:21004', 'health_endpoint': '/health'},
            'frontend': {'url': 'http://localhost:21015', 'health_endpoint': '/'},
            'nginx': {'url': 'http://localhost:21016', 'health_endpoint': '/'},
            'rabbitmq': {'url': 'http://localhost:21001', 'health_endpoint': '/'},
            'mongodb': {'url': 'http://localhost:21003', 'health_endpoint': None},
            'redis': {'url': 'http://localhost:21002', 'health_endpoint': None},
            'gps': {'url': 'http://localhost:21005', 'health_endpoint': '/health'},
            'trip_planning': {'url': 'http://localhost:21006', 'health_endpoint': '/health'},
            'vehicle_maintenance': {'url': 'http://localhost:21007', 'health_endpoint': '/health'},
            'utilities': {'url': 'http://localhost:21008', 'health_endpoint': '/health'},
            'security': {'url': 'http://localhost:21009', 'health_endpoint': '/health'},
            'management': {'url': 'http://localhost:21010', 'health_endpoint': '/health'},
            'micro_frontend': {'url': 'http://localhost:21011', 'health_endpoint': '/health'},
        }
        
        self.api_routes_to_test = [
            '/api/health',
            '/api/vehicles',
            '/api/auth/user-exists',
            '/api/analytics/fleet-utilization'
        ]
    
    async def check_service_health(self, session: aiohttp.ClientSession, name: str, config: Dict) -> Dict:
        """Check health of a single service"""
        result = {
            'name': name,
            'url': config['url'],
            'status': 'unknown',
            'response_time': None,
            'error': None,
            'details': {}
        }
        
        if not config.get('health_endpoint'):
            result['status'] = 'no_health_check'
            return result
        
        try:
            start_time = time.time()
            health_url = f"{config['url']}{config['health_endpoint']}"
            
            async with session.get(health_url, timeout=10) as response:
                response_time = time.time() - start_time
                result['response_time'] = response_time
                
                if response.status == 200:
                    result['status'] = 'healthy'
                    try:
                        result['details'] = await response.json()
                    except:
                        result['details'] = {'response': 'non-json'}
                else:
                    result['status'] = f'unhealthy_http_{response.status}'
                    
        except asyncio.TimeoutError:
            result['status'] = 'timeout'
            result['error'] = 'Service health check timed out'
        except aiohttp.ClientConnectorError as e:
            result['status'] = 'connection_refused'
            result['error'] = f'Connection refused: {str(e)}'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    async def test_api_routing(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Test API routing through core service"""
        results = []
        core_base_url = self.services['core']['url']
        
        for route in self.api_routes_to_test:
            result = {
                'route': route,
                'status': 'unknown',
                'response_time': None,
                'error': None,
                'details': {}
            }
            
            try:
                start_time = time.time()
                url = f"{core_base_url}{route}"
                
                async with session.get(url, timeout=10) as response:
                    response_time = time.time() - start_time
                    result['response_time'] = response_time
                    result['status'] = f'http_{response.status}'
                    
                    try:
                        result['details'] = await response.json()
                    except:
                        result['details'] = {'response': 'non-json'}
                        
            except asyncio.TimeoutError:
                result['status'] = 'timeout'
                result['error'] = 'API call timed out'
            except aiohttp.ClientConnectorError as e:
                result['status'] = 'connection_refused'
                result['error'] = f'Connection refused: {str(e)}'
            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
            
            results.append(result)
        
        return results
    
    async def run_health_check(self) -> Dict:
        """Run complete health check"""
        logger.info("🏥 Starting SAMFMS Health Check...")
        
        async with aiohttp.ClientSession() as session:
            # Check individual services
            service_tasks = [
                self.check_service_health(session, name, config)
                for name, config in self.services.items()
            ]
            
            service_results = await asyncio.gather(*service_tasks, return_exceptions=True)
            
            # Test API routing
            api_results = await self.test_api_routing(session)
        
        # Process results
        healthy_services = [r for r in service_results if isinstance(r, dict) and r['status'] == 'healthy']
        unhealthy_services = [r for r in service_results if isinstance(r, dict) and r['status'] not in ['healthy', 'no_health_check']]
        
        # Generate summary
        summary = {
            'timestamp': time.time(),
            'total_services': len(self.services),
            'healthy_services': len(healthy_services),
            'unhealthy_services': len(unhealthy_services),
            'overall_status': 'healthy' if len(unhealthy_services) == 0 else 'degraded',
            'service_results': service_results,
            'api_routing_results': api_results
        }
        
        return summary
    
    def print_health_report(self, results: Dict):
        """Print formatted health report"""
        print("\n" + "="*60)
        print("🏥 SAMFMS Health Check Report")
        print("="*60)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")
        print(f"Overall Status: {'✅ HEALTHY' if results['overall_status'] == 'healthy' else '⚠️  DEGRADED'}")
        print(f"Services: {results['healthy_services']}/{results['total_services']} healthy")
        
        print("\n📊 Service Status:")
        print("-" * 40)
        
        for service in results['service_results']:
            if isinstance(service, dict):
                status_icon = "✅" if service['status'] == 'healthy' else "❌" if service['status'].startswith('unhealthy') or service['status'] == 'error' else "⚠️"
                response_time = f" ({service['response_time']:.3f}s)" if service['response_time'] else ""
                print(f"{status_icon} {service['name']:15} {service['status']}{response_time}")
                if service.get('error'):
                    print(f"    Error: {service['error']}")
            else:
                print(f"❌ Exception occurred: {service}")
        
        print("\n🔗 API Routing Tests:")
        print("-" * 40)
        
        for api_test in results['api_routing_results']:
            status_icon = "✅" if api_test['status'] == 'http_200' else "❌"
            response_time = f" ({api_test['response_time']:.3f}s)" if api_test['response_time'] else ""
            print(f"{status_icon} {api_test['route']:30} {api_test['status']}{response_time}")
            if api_test.get('error'):
                print(f"    Error: {api_test['error']}")
        
        print("\n" + "="*60)
        
        # Print warnings and recommendations
        if results['unhealthy_services'] > 0:
            print("\n⚠️  Issues Detected:")
            unhealthy = [s for s in results['service_results'] if isinstance(s, dict) and s['status'] not in ['healthy', 'no_health_check']]
            for service in unhealthy:
                print(f"  - {service['name']}: {service['status']}")
                if service.get('error'):
                    print(f"    {service['error']}")
            
            print("\n🔧 Recommendations:")
            print("  1. Check Docker containers are running: docker-compose ps")
            print("  2. Check service logs: docker-compose logs <service-name>")
            print("  3. Restart unhealthy services: docker-compose restart <service-name>")
            print("  4. Verify port availability: netstat -tulpn | grep <port>")

async def main():
    """Main entry point"""
    monitor = ServiceHealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Continuous monitoring mode
        print("🔄 Starting continuous health monitoring (Ctrl+C to stop)...")
        try:
            while True:
                results = await monitor.run_health_check()
                monitor.print_health_report(results)
                print("\n⏰ Next check in 30 seconds...")
                await asyncio.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    else:
        # Single check mode
        results = await monitor.run_health_check()
        monitor.print_health_report(results)
        
        # Exit with error code if services are unhealthy
        if results['overall_status'] != 'healthy':
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
