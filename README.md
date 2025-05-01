# Zabbix AI Agent

Un agente inteligente para Zabbix que utiliza Machine Learning para predecir y detectar anomalías en métricas del sistema.

## 🚀 Características

- Predicción de métricas usando Random Forest
- Detección de anomalías en tiempo real
- Integración nativa con Zabbix
- Soporte específico para Ubuntu 24.04
- Configuración flexible mediante variables de entorno
- Logging detallado y rotación de logs
- Retención configurable de datos históricos

## 📋 Requisitos Previos

- Python 3.8 o superior
- Zabbix Server 6.0 o superior
- Acceso a la API de Zabbix
- Permisos de administrador en Zabbix

## 🔧 Instalación

### En Ubuntu 24.04

```bash
# Clonar el repositorio
git clone https://github.com/sentrait/zabbix-ai-agent.git
cd zabbix-ai-agent

# Ejecutar script de instalación
chmod +x install_ubuntu.sh
./install_ubuntu.sh
```

### Instalación Manual

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| ZABBIX_API_URL | URL de la API de Zabbix | - |
| ZABBIX_USER | Usuario de Zabbix | - |
| ZABBIX_PASSWORD | Contraseña de Zabbix | - |
| LOG_LEVEL | Nivel de logging | INFO |
| MODEL_UPDATE_INTERVAL | Intervalo de actualización del modelo (segundos) | 3600 |
| PREDICTION_INTERVAL | Intervalo de predicción (segundos) | 300 |
| DATA_RETENTION_DAYS | Días de retención de datos | 30 |

## 🔍 Monitoreo

El agente monitorea las siguientes métricas:

- Uso de CPU
- Uso de Memoria
- Uso de Disco
- Tráfico de Red
- Tiempo de Respuesta de Servicios

### Predicciones

El modelo Random Forest se entrena con datos históricos para predecir:

- Tendencias de uso de recursos
- Posibles cuellos de botella
- Anomalías en el comportamiento del sistema

## 📊 Dashboard

El agente incluye templates para Zabbix que proporcionan:

- Visualización de predicciones
- Gráficos de tendencias
- Alertas inteligentes
- Comparación con datos históricos

## 🛠️ Desarrollo

### Estructura del Proyecto

```
zabbix-ai-agent/
├── zabbix_ai_agent.py     # Código principal
├── setup.py               # Configuración de instalación
├── requirements.txt       # Dependencias
├── install_ubuntu.sh      # Script de instalación
├── .env.example          # Plantilla de configuración
├── LICENSE               # Licencia MIT
└── README.md             # Este archivo
```

### Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Soporte

Para soporte, por favor:

1. Revisa la [documentación](https://github.com/sentrait/zabbix-ai-agent/wiki)
2. Abre un [issue](https://github.com/sentrait/zabbix-ai-agent/issues)
3. Contacta a [soporte@sentrait.com.uy](mailto:soporte@sentrait.com.uy)

## 🔜 Próximas Funcionalidades

- [ ] Soporte para más algoritmos de ML
- [ ] API REST para consultas externas
- [ ] Integración con sistemas de notificación
- [ ] Dashboard personalizable
- [ ] Soporte para clustering
- [ ] Exportación de modelos entrenados 