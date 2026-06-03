"""Workers independientes — Consumidores de RabbitMQ.

Cada worker corre como un proceso separado y consume de una cola especifica:
- extract_processor: Procesa archivos Excel cargados
- classification_worker: Clasifica transacciones (hibrido reglas + ML)
- notification_worker: Envia notificaciones push y email
"""
