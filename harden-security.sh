#!/bin/bash

# Security hardening script for AI Stack
# This script applies basic security measures to the host system

set -e

echo "🔒 Applying security hardening measures..."

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "❌ This script must be run as root (sudo)"
        exit 1
    fi
}

# Backup current iptables rules
backup_iptables() {
    echo "📋 Backing up current iptables rules..."
    iptables-save > /etc/iptables/rules.v4.backup.$(date +%Y%m%d_%H%M%S)
    ip6tables-save > /etc/iptables/rules.v6.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
}

# Configure basic firewall rules
configure_firewall() {
    echo "🔥 Configuring firewall rules..."

    # Flush existing rules
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X

    # Default policies
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT

    # Allow loopback
    iptables -A INPUT -i lo -j ACCEPT

    # Allow established connections
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Allow SSH (change port if needed)
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT

    # Allow HTTP and HTTPS for reverse proxy
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT

    # Allow Docker networks (if using docker bridge)
    iptables -A INPUT -i docker0 -j ACCEPT
    iptables -A FORWARD -i docker0 -j ACCEPT
    iptables -A FORWARD -o docker0 -j ACCEPT

    # Rate limiting for SSH
    iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set
    iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 -j DROP

    # Drop invalid packets
    iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

    # Protection against common attacks
    iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,FIN FIN -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,PSH PSH -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,URG URG -j DROP

    # Save rules
    iptables-save > /etc/iptables/rules.v4

    echo "✅ Firewall rules configured"
}

# Configure Docker security
configure_docker_security() {
    echo "🐳 Configuring Docker security..."

    # Create Docker daemon configuration if it doesn't exist
    DOCKER_CONFIG="/etc/docker/daemon.json"
    if [[ ! -f "$DOCKER_CONFIG" ]]; then
        cat > "$DOCKER_CONFIG" << EOF
{
    "icc": false,
    "no-new-privileges": true,
    "userns-remap": "default",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
        echo "✅ Docker daemon security configuration created"
    else
        echo "ℹ️  Docker daemon configuration already exists"
    fi

    # Restart Docker to apply changes
    systemctl restart docker
}

# Configure system security settings
configure_system_security() {
    echo "🛡️  Configuring system security settings..."

    # Disable root login via SSH
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

    # Use strong ciphers for SSH
    echo "Ciphers aes128-ctr,aes192-ctr,aes256-ctr" >> /etc/ssh/sshd_config
    echo "MACs hmac-sha2-256,hmac-sha2-512" >> /etc/ssh/sshd_config

    # Restart SSH
    systemctl restart sshd

    echo "✅ System security settings configured"
}

# Main execution
main() {
    check_root
    backup_iptables
    configure_firewall
    configure_docker_security
    configure_system_security

    echo ""
    echo "🎉 Security hardening completed!"
    echo ""
    echo "⚠️  IMPORTANT NOTES:"
    echo "1. Test SSH access before closing this session"
    echo "2. Update monitoring credentials in .env file"
    echo "3. Review and customize firewall rules for your needs"
    echo "4. Consider enabling SELinux or AppArmor for additional security"
    echo "5. Regularly update your system and Docker images"
}

# Run main function
main "$@"