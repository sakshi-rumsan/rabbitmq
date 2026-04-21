PIPELINE_EXCHANGE = "pipeline.events"
EXCHANGE_TYPE = "topic"

# Routing keys
RK_ORDER_CREATED = "order.created"
RK_INVENTORY_RESERVED = "inventory.reserved"
RK_INVENTORY_FAILED = "inventory.failed"
RK_PAYMENT_SUCCESS = "payment.success"
RK_PAYMENT_FAILED = "payment.failed"
RK_ORDER_SHIPPED = "order.shipped"

# Queue names
Q_INVENTORY = "inventory.queue"
Q_PAYMENT = "payment.queue"
Q_SHIPPING = "shipping.queue"
Q_NOTIFICATION = "notification.queue"
Q_ORDER_UPDATE = "order.update.queue"
Q_DLQ = "dlq.queue"
