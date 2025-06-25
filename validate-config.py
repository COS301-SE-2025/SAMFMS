#!/usr/bin/env python3
"""
SAMFMS Configuration Validator
============================

This script validates environment configuration files to ensure all required
variables are set and have valid values before starting the application.

Usage:
    python validate-config.py [--env development|production]
"""

import os
import sys
import argparse
import re
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse


class ConfigValidator:
    """Validates SAMFMS environment configuration."""
    
    def __init__(self, env_file: str):
        self.env_file = env_file
        self.config = {}
        self.errors = []
        self.warnings = []
        
    def load_config(self) -> None:
        """Load configuration from environment file."""
        if not os.path.exists(self.env_file):
            self.errors.append(f"Environment file not found: {self.env_file}")
            return
            
        with open(self.env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.config[key.strip()] = value.strip()
    
    def validate_required_variables(self) -> None:
        """Validate that all required environment variables are present."""
        required_vars = [
            'ENVIRONMENT',
            'JWT_SECRET_KEY',
            'MONGODB_URL',
            'RABBITMQ_URL',
            'REDIS_HOST',
            'CORE_PORT',
            'SECURITY_SERVICE_PORT'
        ]
        
        for var in required_vars:
            if var not in self.config or not self.config[var]:
                self.errors.append(f"Required variable '{var}' is missing or empty")
    
    def validate_ports(self) -> None:
        """Validate port configurations."""
        port_vars = [k for k in self.config.keys() if 'PORT' in k]
        used_ports = set()
        
        for port_var in port_vars:
            port_value = self.config[port_var]
            try:
                port = int(port_value)
                if port < 1 or port > 65535:
                    self.errors.append(f"Invalid port range for {port_var}: {port}")
                elif port in used_ports:
                    self.errors.append(f"Port conflict: {port} used by multiple services")
                else:
                    used_ports.add(port)
            except ValueError:
                self.errors.append(f"Invalid port value for {port_var}: {port_value}")
    
    def validate_urls(self) -> None:
        """Validate URL configurations."""
        url_vars = [k for k in self.config.keys() if 'URL' in k]
        
        for url_var in url_vars:
            url_value = self.config[url_var]
            try:
                parsed = urlparse(url_value)
                if not parsed.scheme:
                    self.errors.append(f"Invalid URL format for {url_var}: missing scheme")
                if not parsed.netloc:
                    self.errors.append(f"Invalid URL format for {url_var}: missing host")
            except Exception as e:
                self.errors.append(f"Invalid URL for {url_var}: {str(e)}")
    
    def validate_security_config(self) -> None:
        """Validate security-related configurations."""
        environment = self.config.get('ENVIRONMENT', '')
        
        # JWT Secret validation
        jwt_secret = self.config.get('JWT_SECRET_KEY', '')
        if environment == 'production':
            if 'change' in jwt_secret.lower() or 'default' in jwt_secret.lower():
                self.errors.append("JWT_SECRET_KEY must be changed for production")
            if len(jwt_secret) < 32:
                self.errors.append("JWT_SECRET_KEY should be at least 32 characters long")
        
        # Password validation for production
        if environment == 'production':
            password_vars = ['RABBITMQ_PASSWORD', 'MONGODB_PASSWORD', 'REDIS_PASSWORD']
            for var in password_vars:
                password = self.config.get(var, '')
                if 'CHANGE' in password or len(password) < 8:
                    self.errors.append(f"{var} must be set to a strong password for production")
        
        # Email configuration
        if environment == 'production':
            email_vars = ['SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
            for var in email_vars:
                if var not in self.config or 'CHANGE' in self.config.get(var, ''):
                    self.errors.append(f"{var} must be configured for production")
    
    def validate_database_config(self) -> None:
        """Validate database configurations."""
        mongodb_url = self.config.get('MONGODB_URL', '')
        if mongodb_url:
            try:
                parsed = urlparse(mongodb_url)
                if parsed.scheme != 'mongodb':
                    self.errors.append("MONGODB_URL must use mongodb:// scheme")
            except Exception as e:
                self.errors.append(f"Invalid MONGODB_URL: {str(e)}")
        
        # Check database naming consistency
        environment = self.config.get('ENVIRONMENT', '')
        db_prefix = self.config.get('MONGODB_DATABASE_PREFIX', '')
        if environment and db_prefix:
            expected_prefix = f"samfms_{environment[:4]}"  # samfms_dev or samfms_prod
            if not db_prefix.startswith(expected_prefix):
                self.warnings.append(f"Database prefix '{db_prefix}' doesn't match environment '{environment}'")
    
    def validate_environment_specific(self) -> None:
        """Validate environment-specific configurations."""
        environment = self.config.get('ENVIRONMENT', '')
        
        if environment == 'development':
            # Development-specific validations
            if self.config.get('DEBUG') != 'true':
                self.warnings.append("DEBUG should be 'true' in development")
            if self.config.get('LOG_LEVEL') not in ['DEBUG', 'INFO']:
                self.warnings.append("LOG_LEVEL should be 'DEBUG' or 'INFO' in development")
        
        elif environment == 'production':
            # Production-specific validations
            if self.config.get('DEBUG') == 'true':
                self.errors.append("DEBUG must be 'false' in production")
            if self.config.get('LOG_LEVEL') == 'DEBUG':
                self.warnings.append("LOG_LEVEL should not be 'DEBUG' in production")
            if self.config.get('HOT_RELOAD') == 'true':
                self.warnings.append("HOT_RELOAD should be 'false' in production")
    
    def validate(self) -> bool:
        """Run all validations and return True if configuration is valid."""
        self.load_config()
        
        if self.errors:  # If loading failed, don't proceed
            return False
        
        self.validate_required_variables()
        self.validate_ports()
        self.validate_urls()
        self.validate_security_config()
        self.validate_database_config()
        self.validate_environment_specific()
        
        return len(self.errors) == 0
    
    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("❌ Configuration Validation Failed")
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Configuration validation passed!")
        elif not self.errors:
            print("✅ Configuration validation passed with warnings.")


def main():
    parser = argparse.ArgumentParser(description='Validate SAMFMS configuration')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Environment to validate')
    parser.add_argument('--file', help='Specific .env file to validate')
    
    args = parser.parse_args()
    
    if args.file:
        env_file = args.file
    else:
        env_file = f'.env.{args.env}'
    
    validator = ConfigValidator(env_file)
    is_valid = validator.validate()
    validator.print_results()
    
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
