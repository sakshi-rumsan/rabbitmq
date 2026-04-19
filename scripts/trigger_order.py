import json
from services.order_service.app.api.order_routes import create_order_service

# Load dummy order data from JSON file
def main():
    with open('data/dummy_order.json') as f:
        order_data = json.load(f)
    response = create_order_service(order_data)
    print('Order created:', response)

if __name__ == "__main__":
    main()
