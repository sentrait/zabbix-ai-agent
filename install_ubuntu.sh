#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Instalando Zabbix AI Agent...${NC}"

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script debe ejecutarse como root${NC}"
    exit 1
fi

# Verificar la versión de Ubuntu
if ! grep -q "Ubuntu 24.04" /etc/os-release; then
    echo -e "${RED}Este script está diseñado para Ubuntu 24.04${NC}"
    echo -e "${RED}Tu versión de Ubuntu es:${NC}"
    cat /etc/os-release | grep VERSION=
    exit 1
fi

# Instalar dependencias del sistema
echo -e "${GREEN}Instalando dependencias del sistema...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Crear directorio de instalación
echo -e "${GREEN}Creando directorios...${NC}"
mkdir -p /opt/zabbix-ai-agent
mkdir -p /etc/zabbix-ai-agent
mkdir -p /var/log/zabbix-ai-agent

# Crear entorno virtual
echo -e "${GREEN}Creando entorno virtual...${NC}"
python3 -m venv /opt/zabbix-ai-agent/venv

# Activar entorno virtual e instalar el agente
echo -e "${GREEN}Instalando el agente...${NC}"
source /opt/zabbix-ai-agent/venv/bin/activate
pip install .

# Crear archivo de configuración
echo -e "${GREEN}Creando archivo de configuración...${NC}"
cat > /etc/zabbix-ai-agent/.env << EOL
# URL del servidor Zabbix
ZABBIX_URL=https://zabbix.sentrait.com.uy/api_jsonrpc.php
ZABBIX_USER=Admin
ZABBIX_PASSWORD=ko0XxG1h\$Y2W42

# Configuración del modelo de IA
ALERT_THRESHOLD=90
MONITORING_INTERVAL=15
TRAINING_PERIOD=30
PREDICTION_PERIOD=24

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/zabbix-ai-agent/zabbix_ai_agent.log
EOL

# Crear servicio systemd
echo -e "${GREEN}Creando servicio systemd...${NC}"
cat > /etc/systemd/system/zabbix-ai-agent.service << EOL
[Unit]
Description=Zabbix AI Agent
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/zabbix-ai-agent
Environment=PATH=/opt/zabbix-ai-agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/opt/zabbix-ai-agent
ExecStart=/opt/zabbix-ai-agent/venv/bin/python -m zabbix_ai_agent
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Establecer permisos
echo -e "${GREEN}Configurando permisos...${NC}"
chmod 600 /etc/zabbix-ai-agent/.env
chmod 644 /etc/systemd/system/zabbix-ai-agent.service
chown -R root:root /opt/zabbix-ai-agent
chown -R root:root /etc/zabbix-ai-agent
chown -R root:root /var/log/zabbix-ai-agent

# Recargar systemd y habilitar el servicio
echo -e "${GREEN}Habilitando y iniciando el servicio...${NC}"
systemctl daemon-reload
systemctl enable zabbix-ai-agent
systemctl start zabbix-ai-agent

echo -e "${GREEN}Instalación completada${NC}"
echo -e "${GREEN}Para ver el estado del servicio:${NC} systemctl status zabbix-ai-agent"
echo -e "${GREEN}Para ver los logs:${NC} tail -f /var/log/zabbix-ai-agent/zabbix_ai_agent.log" 