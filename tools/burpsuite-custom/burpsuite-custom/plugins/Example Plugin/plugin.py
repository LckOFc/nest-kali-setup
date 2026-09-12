
class MyPlugin:
    name = "Example Plugin"
    description = "Demonstracao de plugin CustomBurp"
    author = "ratman4080"
    version = "1.0.0"
    
    def on_http_send(self, request):
        print(f"[{self.name}] Sending: {request.get('method')} {request.get('path')}")
        return request
    
    def on_http_received(self, response):
        print(f"[{self.name}] Received: {response.get('status_code')}")
        return response
    
    def on_proxy_request(self, request):
        # Pode modificar request antes de enviar
        return request
    
    def on_proxy_response(self, response):
        # Pode modificar response antes de mostrar
        return response
