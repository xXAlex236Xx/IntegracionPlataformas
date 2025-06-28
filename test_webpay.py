# test_webpay.py
import os
from transbank.webpay.webpay_plus.transaction import Transaction

# Simula los valores de settings.py y los argumentos
# Asegúrate de usar tus credenciales REALES de INTEGRACION aquí
TBK_COMMERCE_CODE = "602330089855" # Tu código de comercio
TBK_API_KEY = "071112270966952F87A76D92ED9C623C" # Tu API Key
TBK_ENVIRONMENT = "INTEGRACION" # Tu entorno

# Valores de ejemplo para la transacción
test_buy_order = "test_order_" + str(os.urandom(4).hex())
test_session_id = "test_session_" + str(os.urandom(4).hex())
test_amount = 10000.00
test_return_url = "http://127.0.0.1:8000/webpay/confirmar_pago/" # La URL que usas

print("--- Iniciando prueba de Transbank SDK ---")
print(f"Comercio: {TBK_COMMERCE_CODE}")
print(f"API Key: {TBK_API_KEY}")
print(f"Entorno: {TBK_ENVIRONMENT}")
print(f"return_url de prueba: {test_return_url}")

try:
    # Configuración de la clase Transaction
    Transaction.commerce_code = TBK_COMMERCE_CODE
    Transaction.api_key = TBK_API_KEY
    Transaction.environment = TBK_ENVIRONMENT

    print("\nDEBUG (test_webpay.py):")
    print(f"Type of test_buy_order: {type(test_buy_order)}, Value: {test_buy_order}")
    print(f"Type of test_session_id: {type(test_session_id)}, Value: {test_session_id}")
    print(f"Type of test_amount: {type(test_amount)}, Value: {test_amount}")
    print(f"Type of test_return_url: {type(test_return_url)}, Value: {test_return_url}")

    # Intenta crear la transacción
    response = Transaction.create(test_buy_order, test_session_id, test_amount, test_return_url)

    print("\n--- Transacción creada exitosamente en test_webpay.py ---")
    print(f"URL: {response['url']}")
    print(f"Token: {response['token']}")

except Exception as e:
    print("\n--- ERROR al crear transacción en test_webpay.py ---")
    print(f"Error: {e}")

print("--- Fin prueba de Transbank SDK ---")