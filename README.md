# Agente de IA para Zabbix

Este agente de IA se conecta a tu servidor Zabbix para analizar datos históricos y predecir posibles problemas futuros utilizando aprendizaje automático.

## Características

- Conexión automática a la API de Zabbix
- Análisis de datos históricos
- Predicción de problemas utilizando Random Forest
- Monitoreo en tiempo real
- Sistema de alertas automáticas
- Logging detallado de operaciones
- Configuración flexible mediante variables de entorno
- Instalación automatizada para Ubuntu 24.04

## Requisitos

- Python 3.8 o superior
- Acceso a un servidor Zabbix con API habilitada
- Credenciales de Zabbix con permisos de lectura

## Instalación

### En Ubuntu 24.04

1. Descarga el paquete del agente:
```bash
git clone https://github.com/sentrait/zabbix-ai-agent.git
cd zabbix-ai-agent
```

2. Ejecuta el script de instalación como root:
```bash
sudo bash install_ubuntu.sh
```

El script realizará automáticamente:
- Instalación de dependencias necesarias
- Creación de directorios y archivos de configuración
- Configuración del servicio systemd
- Inicio automático del agente

### Instalación Manual (Windows u otros sistemas)

1. Clona o descarga este repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno:
   - Crea un archivo `.env` en el directorio raíz
   - Añade las siguientes variables:

```ini
# URL del servidor Zabbix (debe terminar en api_jsonrpc.php)
ZABBIX_URL=https://your-zabbix-server/api_jsonrpc.php

# Credenciales de acceso
ZABBIX_USER=your_username
ZABBIX_PASSWORD=your_password

# Configuración del modelo de IA
# Umbral de alerta (valor entre 0 y 100)
ALERT_THRESHOLD=90

# Intervalo de monitoreo en minutos
MONITORING_INTERVAL=15

# Período de datos históricos para entrenamiento (en días)
TRAINING_PERIOD=30

# Período de predicción (en horas)
PREDICTION_PERIOD=24

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=zabbix_ai_agent.log
```

### Descripción de las Variables de Entorno

- `ZABBIX_URL`: URL completa de la API de Zabbix
- `ZABBIX_USER`: Nombre de usuario con acceso a la API
- `ZABBIX_PASSWORD`: Contraseña del usuario

#### Configuración del Modelo
- `ALERT_THRESHOLD`: Valor numérico (0-100) que determina cuándo se genera una alerta
- `MONITORING_INTERVAL`: Frecuencia de monitoreo en minutos
- `TRAINING_PERIOD`: Cantidad de días de datos históricos para entrenar el modelo
- `PREDICTION_PERIOD`: Ventana de tiempo en horas para las predicciones

#### Configuración de Logs
- `LOG_LEVEL`: Nivel de detalle de los logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE`: Nombre del archivo donde se guardarán los logs

## Gestión del Servicio en Ubuntu

### Comandos Útiles

```bash
# Ver el estado del servicio
sudo systemctl status zabbix-ai-agent

# Iniciar el servicio
sudo systemctl start zabbix-ai-agent

# Detener el servicio
sudo systemctl stop zabbix-ai-agent

# Reiniciar el servicio
sudo systemctl restart zabbix-ai-agent

# Ver los logs en tiempo real
sudo tail -f /var/log/zabbix-ai-agent/zabbix_ai_agent.log
```

### Ubicación de Archivos en Ubuntu

- Ejecutable: `/opt/zabbix-ai-agent/venv/bin/zabbix-ai-agent`
- Configuración: `/etc/zabbix-ai-agent/.env`
- Logs: `/var/log/zabbix-ai-agent/zabbix_ai_agent.log`
- Servicio: `/etc/systemd/system/zabbix-ai-agent.service`

## Uso

Para iniciar el agente:

```bash
python zabbix_ai_agent.py
```

El agente:
- Se conectará automáticamente a tu servidor Zabbix
- Recopilará datos históricos según el período configurado
- Entrenará modelos de IA para cada item monitoreado
- Realizará predicciones según el intervalo configurado
- Generará alertas cuando los valores predichos superen el umbral establecido

## Logs

Los logs se guardan en el archivo especificado en `LOG_FILE` y contienen información detallada sobre:
- Conexiones a Zabbix
- Entrenamiento de modelos
- Predicciones
- Alertas
- Errores

## Personalización

Puedes ajustar el comportamiento del agente modificando las variables en el archivo `.env`:

1. **Ajuste de Sensibilidad**
   - Reduce `ALERT_THRESHOLD` para recibir más alertas
   - Aumenta `ALERT_THRESHOLD` para recibir solo alertas críticas

2. **Frecuencia de Monitoreo**
   - Reduce `MONITORING_INTERVAL` para actualizaciones más frecuentes
   - Aumenta `MONITORING_INTERVAL` para reducir la carga del servidor

3. **Precisión del Modelo**
   - Aumenta `TRAINING_PERIOD` para un modelo más preciso (requiere más datos)
   - Ajusta `PREDICTION_PERIOD` según tus necesidades de predicción

4. **Nivel de Logging**
   - Usa `LOG_LEVEL=DEBUG` para diagnóstico detallado
   - Usa `LOG_LEVEL=WARNING` para ver solo problemas importantes 