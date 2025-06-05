import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import schedule
import time

# Cargar variables de entorno
load_dotenv()

# Configurar logging con nivel desde .env
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'zabbix_ai_agent.log')),
        logging.StreamHandler()
    ]
)

# Configuración de Zabbix
ZABBIX_URL = "https://zabbix.sentrait.com.uy/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "ko0XxG1h$Y2W42"

class ZabbixAIAgent:
    def __init__(self):
        self.zapi = None
        self.scaler = MinMaxScaler()
        self.model = None
        # Cargar configuración desde .env
        self.alert_threshold = float(os.getenv('ALERT_THRESHOLD', 90))
        self.training_period = int(os.getenv('TRAINING_PERIOD', 30))
        self.prediction_period = int(os.getenv('PREDICTION_PERIOD', 24))
        self.monitoring_interval = int(os.getenv('MONITORING_INTERVAL', 15))
        self.connect_to_zabbix()
        self.initialize_model()

    def connect_to_zabbix(self):
        """Conectar a la API de Zabbix"""
        try:
            logging.info(f"Intentando conectar a Zabbix en: {os.getenv('ZABBIX_URL')}")
            self.zapi = ZabbixAPI(os.getenv('ZABBIX_URL'))
            self.zapi.login(os.getenv('ZABBIX_USER'), os.getenv('ZABBIX_PASSWORD'))
            logging.info(f"Conectado exitosamente a Zabbix API Version {self.zapi.api_version()}")
        except Exception as e:
            logging.error(f"Error al conectar con Zabbix: {e}")
            raise

    def get_historical_data(self, host_id, item_key, time_from):
        """Obtener datos históricos de Zabbix"""
        try:
            logging.info(f"Obteniendo datos históricos para host_id: {host_id}, item_key: {item_key}")
            items = self.zapi.item.get(
                hostids=host_id,
                search={'key_': item_key},
                output=['itemid']
            )
            
            if not items:
                logging.error(f"No se encontró el item con key {item_key}")
                return None

            history = self.zapi.history.get(
                itemids=items[0]['itemid'],
                time_from=time_from,
                output='extend',
                sortfield='clock',
                sortorder='ASC'
            )

            if history:
                logging.info(f"Se obtuvieron {len(history)} registros históricos")
            else:
                logging.warning(f"No se encontraron datos históricos para el item")

            return pd.DataFrame(history)
        except Exception as e:
            logging.error(f"Error al obtener datos históricos: {e}")
            return None

    def initialize_model(self):
        """Inicializar el modelo de IA"""
        try:
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            logging.info("Modelo de IA inicializado correctamente")
        except Exception as e:
            logging.error(f"Error al inicializar el modelo: {e}")
            raise

    def train_model(self, host_id, item_key):
        """Entrenar el modelo con datos históricos"""
        time_from = int((datetime.now() - timedelta(days=self.training_period)).timestamp())
        logging.info(f"Iniciando entrenamiento para host_id: {host_id}, item_key: {item_key}")
        
        data = self.get_historical_data(host_id, item_key, time_from)
        
        if data is None or data.empty:
            logging.warning(f"No hay suficientes datos para entrenar el modelo")
            return False

        try:
            # Preparar datos para el entrenamiento
            values = data['value'].astype(float).values.reshape(-1, 1)
            scaled_values = self.scaler.fit_transform(values)
            
            # Crear secuencias para el entrenamiento
            X, y = [], []
            for i in range(len(scaled_values) - self.prediction_period):
                X.append(scaled_values[i:i+self.prediction_period].flatten())
                y.append(scaled_values[i+self.prediction_period][0])
            
            if not X:
                logging.warning("No hay suficientes secuencias para entrenar el modelo")
                return False

            X = np.array(X)
            y = np.array(y)

            # Entrenar el modelo
            self.model.fit(X, y)
            logging.info(f"Modelo entrenado exitosamente con {len(X)} secuencias")
            return True
        except Exception as e:
            logging.error(f"Error durante el entrenamiento: {e}")
            return False

    def predict_problems(self, host_id, item_key):
        """Predecir problemas futuros"""
        time_from = int((datetime.now() - timedelta(hours=self.prediction_period)).timestamp())
        logging.info(f"Realizando predicción para host_id: {host_id}, item_key: {item_key}")
        
        data = self.get_historical_data(host_id, item_key, time_from)
        
        if data is None or data.empty:
            logging.warning("No hay datos suficientes para realizar predicción")
            return None

        try:
            values = data['value'].astype(float).values.reshape(-1, 1)
            scaled_values = self.scaler.transform(values)
            
            # Preparar datos para la predicción
            if len(scaled_values) < self.prediction_period:
                logging.warning("No hay suficientes datos para realizar predicción")
                return None
                
            X = scaled_values[-self.prediction_period:].flatten().reshape(1, -1)
            
            # Realizar predicción
            prediction = self.model.predict(X)
            prediction = self.scaler.inverse_transform(prediction.reshape(-1, 1))
            
            logging.info(f"Predicción realizada: {prediction[0][0]}")
            return prediction[0][0]
        except Exception as e:
            logging.error(f"Error durante la predicción: {e}")
            return None

    def monitor_and_predict(self):
        """Monitorear y predecir problemas en tiempo real"""
        try:
            logging.info("Iniciando ciclo de monitoreo y predicción")
            hosts = self.zapi.host.get(output=['hostid', 'host'])
            logging.info(f"Se encontraron {len(hosts)} hosts para analizar")

            for host in hosts:
                logging.info(f"Analizando host: {host['host']}")
                items = self.zapi.item.get(
                    hostids=host['hostid'],
                    output=['key_', 'name']
                )
                logging.info(f"Se encontraron {len(items)} items para el host {host['host']}")
                
                for item in items:
                    logging.info(f"Procesando item: {item['name']}")
                    # Entrenar el modelo para cada item
                    if self.train_model(host['hostid'], item['key_']):
                        # Realizar predicción
                        prediction = self.predict_problems(host['hostid'], item['key_'])
                        if prediction is not None:
                            logging.info(f"Predicción para {host['host']} - {item['name']}: {prediction}")
                            
                            # Analizar si el valor predicho indica un problema potencial
                            if prediction > self.alert_threshold:
                                logging.warning(f"¡ALERTA! Posible problema futuro detectado en {host['host']} - {item['name']}")
                                
        except Exception as e:
            logging.error(f"Error en el monitoreo: {e}")

def main():
    logging.info("Iniciando el agente de IA para Zabbix")
    agent = ZabbixAIAgent()
    
    # Ejecutar el primer monitoreo inmediatamente
    logging.info("Ejecutando primer ciclo de monitoreo")
    agent.monitor_and_predict()
    
    # Programar la ejecución del monitoreo según el intervalo configurado
    schedule.every(agent.monitoring_interval).minutes.do(agent.monitor_and_predict)
    logging.info(f"Monitoreo programado cada {agent.monitoring_interval} minutos")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 