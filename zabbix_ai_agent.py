import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import schedule
import time
import joblib

# Cargar variables de entorno
load_dotenv()

# Configurar logging con nivel desde .env
log_file_path = os.getenv('LOG_FILE', 'zabbix_ai_agent.log')
log_max_bytes = int(os.getenv('LOG_MAX_BYTES', 10*1024*1024)) # Default 10MB
log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', 5))

rotating_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=log_max_bytes,
    backupCount=log_backup_count
)

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)

# Configuración de Zabbix

class ZabbixAIAgent:
    def __init__(self):
        self.zabbix_url = os.getenv('ZABBIX_API_URL')
        self.zabbix_user = os.getenv('ZABBIX_USER')
        self.zabbix_password = os.getenv('ZABBIX_PASSWORD')

        if not all([self.zabbix_url, self.zabbix_user, self.zabbix_password]):
            raise ValueError("Missing one or more Zabbix configuration environment variables (ZABBIX_API_URL, ZABBIX_USER, ZABBIX_PASSWORD)")

        self.zapi = None
        self.models = {}
        self.scalers = {}
        self.model_dir = os.getenv('MODEL_DIR', 'trained_models')
        os.makedirs(self.model_dir, exist_ok=True)
        self.last_trained_times = {}
        # Cargar configuración desde .env
        self.alert_threshold = float(os.getenv('ALERT_THRESHOLD', 90))
        self.training_period = int(os.getenv('TRAINING_PERIOD', 30)) # Days of data for training
        self.model_sequence_length = int(os.getenv('MODEL_SEQUENCE_LENGTH', '24')) # Number of data points in a sequence for the model
        self.prediction_data_lookback_hours = int(os.getenv('PREDICTION_DATA_LOOKBACK_HOURS', '24')) # Hours of recent data to use for making a prediction
        self.monitoring_interval = int(os.getenv('MONITORING_INTERVAL', 15))
        self.model_update_interval = int(os.getenv('MODEL_UPDATE_INTERVAL', '3600'))
        self.connect_to_zabbix()

    def connect_to_zabbix(self):
        """Conectar a la API de Zabbix"""
        try:
            logging.info(f"Intentando conectar a Zabbix en: {self.zabbix_url}")
            self.zapi = ZabbixAPI(self.zabbix_url)
            self.zapi.login(self.zabbix_user, self.zabbix_password)
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
                logging.warning(f"No item found with key {item_key} for host_id {host_id}")
                return pd.DataFrame()

            history = self.zapi.history.get(
                itemids=items[0]['itemid'],
                time_from=time_from,
                output='extend',
                sortfield='clock',
                sortorder='ASC'
            )

            if not history:
                logging.warning(f"No historical data found for item_id {items[0]['itemid']}")
                return pd.DataFrame()

            logging.info(f"Se obtuvieron {len(history)} registros históricos")
            return pd.DataFrame(history)
        except Exception as e:
            logging.error(f"Error al obtener datos históricos: {e}")
            return pd.DataFrame()

    def _get_model_path(self, item_id_key):
        """Devuelve la ruta del archivo para el modelo de un item."""
        return os.path.join(self.model_dir, f"{item_id_key}_model.joblib")

    def _get_scaler_path(self, item_id_key):
        """Devuelve la ruta del archivo para el scaler de un item."""
        return os.path.join(self.model_dir, f"{item_id_key}_scaler.joblib")

    def _load_model_and_scaler(self, item_id_key):
        """Carga el modelo y el scaler para un item_id_key dado."""
        model_path = self._get_model_path(item_id_key)
        scaler_path = self._get_scaler_path(item_id_key)

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.models[item_id_key] = joblib.load(model_path)
                self.scalers[item_id_key] = joblib.load(scaler_path)
                logging.info(f"Modelo y scaler cargados para {item_id_key} desde {self.model_dir}")
                return True
            except Exception as e:
                logging.error(f"Error al cargar modelo/scaler para {item_id_key}: {e}")
                return False
        else:
            logging.info(f"Modelo y/o scaler no encontrados para {item_id_key} en {self.model_dir}. Se creará uno nuevo si es necesario.")
            return False

    def _save_model_and_scaler(self, item_id_key):
        """Guarda el modelo y el scaler para un item_id_key dado."""
        model_path = self._get_model_path(item_id_key)
        scaler_path = self._get_scaler_path(item_id_key)

        try:
            joblib.dump(self.models[item_id_key], model_path)
            joblib.dump(self.scalers[item_id_key], scaler_path)
            logging.info(f"Modelo y scaler guardados para {item_id_key} en {self.model_dir}")
        except Exception as e:
            logging.error(f"Error al guardar modelo/scaler para {item_id_key}: {e}")

    def train_model(self, host_id, item_key):
        """Entrenar el modelo con datos históricos"""
        item_id_key = f"{host_id}_{item_key}"
        time_from = int((datetime.now() - timedelta(days=self.training_period)).timestamp())
        logging.info(f"Iniciando entrenamiento para {item_id_key}")

        if not self._load_model_and_scaler(item_id_key):
            logging.info(f"Creando nuevo modelo y scaler para {item_id_key}")
            current_model = RandomForestRegressor(n_estimators=100, random_state=42)
            current_scaler = MinMaxScaler()
            self.models[item_id_key] = current_model
            self.scalers[item_id_key] = current_scaler
        else:
            logging.info(f"Usando modelo y scaler existentes para {item_id_key}")
            current_model = self.models[item_id_key]
            current_scaler = self.scalers[item_id_key]
        
        data = self.get_historical_data(host_id, item_key, time_from)
        
        if data is None or data.empty: # data.empty will be true if get_historical_data returns pd.DataFrame()
            logging.warning(f"No historical data available for training {item_id_key}. Skipping training.")
            return False

        try:
            # Preparar datos para el entrenamiento
            values = data['value'].astype(float).values.reshape(-1, 1)
            scaled_values = current_scaler.fit_transform(values)
            
            # Crear secuencias para el entrenamiento
            X, y = [], []
            for i in range(len(scaled_values) - self.model_sequence_length):
                X.append(scaled_values[i:i+self.model_sequence_length].flatten())
                y.append(scaled_values[i+self.model_sequence_length][0])
            
            if not X or not y: # Asegurarse que y no esté vacío también
                logging.warning(f"No hay suficientes secuencias ({len(X)}) para entrenar el modelo para {item_id_key}")
                return False

            X = np.array(X)
            y = np.array(y)

            # Entrenar el modelo
            current_model.fit(X, y)
            logging.info(f"Modelo para {item_id_key} entrenado exitosamente con {len(X)} secuencias")
            self._save_model_and_scaler(item_id_key)
            return True
        except Exception as e:
            logging.error(f"Error durante el entrenamiento para {item_id_key}: {e}")
            return False

    def predict_problems(self, host_id, item_key):
        """Predecir problemas futuros"""
        item_id_key = f"{host_id}_{item_key}"
        logging.info(f"Realizando predicción para {item_id_key} (data lookback: {self.prediction_data_lookback_hours}h)")

        if not self._load_model_and_scaler(item_id_key) or item_id_key not in self.models:
            logging.warning(f"Modelo para {item_id_key} no encontrado o no cargado. Skipping predicción.")
            return None

        current_model = self.models[item_id_key]
        current_scaler = self.scalers[item_id_key]

        time_from = int((datetime.now() - timedelta(hours=self.prediction_data_lookback_hours)).timestamp())
        data = self.get_historical_data(host_id, item_key, time_from)
        
        if data is None or data.empty: # data.empty will be true if get_historical_data returns pd.DataFrame()
            logging.warning(f"No historical data available for prediction for {item_id_key}. Skipping prediction.")
            return None

        try:
            values = data['value'].astype(float).values.reshape(-1, 1)
            # Asegurarse de que el scaler esté ajustado (fit) antes de transformar.
            # Esto debería haber ocurrido en train_model. Si no, es un problema de flujo.
            # Por seguridad, podríamos verificar current_scaler.n_samples_seen_ > 0 pero puede ser ruidoso.
            scaled_values = current_scaler.transform(values)
            
            # Preparar datos para la predicción
            if len(scaled_values) < self.model_sequence_length:
                logging.warning(f"No hay suficientes datos (got {len(scaled_values)}, need {self.model_sequence_length}) para realizar predicción con la secuencia completa para {item_id_key}.")
                return None
                
            X_pred = scaled_values[-self.model_sequence_length:].flatten().reshape(1, -1)
            
            # Realizar predicción
            prediction = current_model.predict(X_pred)
            prediction_inversed = current_scaler.inverse_transform(prediction.reshape(-1, 1))
            
            logging.info(f"Predicción para {item_id_key} realizada: {prediction_inversed[0][0]}")
            return prediction_inversed[0][0]
        except Exception as e:
            logging.error(f"Error durante la predicción para {item_id_key}: {e}")
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
                    item_id_key = f"{host['hostid']}_{item['key_']}"
                    current_timestamp = time.time()
                    last_trained = self.last_trained_times.get(item_id_key, 0)

                    if (current_timestamp - last_trained) > self.model_update_interval:
                        logging.info(f"Intervalo de entrenamiento caducado para {item_id_key}. Entrenando modelo.")
                        if self.train_model(host['hostid'], item['key_']):
                            self.last_trained_times[item_id_key] = current_timestamp
                    else:
                        logging.info(f"Modelo para {item_id_key} está actualizado. Saltando entrenamiento.")

                    # Realizar predicción independientemente del ciclo de entrenamiento
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