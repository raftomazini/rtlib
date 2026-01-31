import http.server
import socketserver
import urllib.parse
import urllib.request
import webbrowser
import json
import sys

# Configurações do servidor local para receber o callback
PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}"

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Captura o código da URL de retorno
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            
            # Resposta para o navegador
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Autenticacao concluida!</h1><p>Voce pode fechar esta janela e voltar ao terminal.</p>")
        else:
            self.send_response(400)
            self.wfile.write(b"<h1>Erro: Codigo nao encontrado na URL.</h1>")

    def log_message(self, format, *args):
        # Silencia logs do servidor para não poluir o terminal
        pass

def get_google_config():
    return {
        'auth_endpoint': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_endpoint': 'https://oauth2.googleapis.com/token',
        'scope': 'https://mail.google.com/',
        # access_type=offline e prompt=consent são obrigatórios para receber refresh_token do Google
        'extra_params': {'access_type': 'offline', 'prompt': 'consent'}
    }

def get_microsoft_config():
    return {
        'auth_endpoint': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_endpoint': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        # offline_access é obrigatório para receber refresh_token da Microsoft
        'scope': 'SMTP.Send offline_access',
        'extra_params': {}
    }

def main():
    print("--- Gerador de Refresh Token OAuth2 ---")
    print("IMPORTANTE: Certifique-se de que 'http://localhost:8080' esta adicionado")
    print("como 'URI de Redirecionamento' (Redirect URI) no console do seu provedor (Google/Azure).\n")

    print("Escolha o provedor:")
    print("1 - Google (Gmail)")
    print("2 - Microsoft (Outlook/Office365)")
    
    choice = input("Opcao: ").strip()
    
    if choice == '1':
        config = get_google_config()
    elif choice == '2':
        config = get_microsoft_config()
    else:
        print("Opcao invalida.")
        return

    client_id = input("\nDigite o Client ID: ").strip()
    client_secret = input("Digite o Client Secret: ").strip()

    # 1. Montar URL de Autorização
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': config['scope'],
    }
    params.update(config['extra_params'])
    
    auth_url = f"{config['auth_endpoint']}?{urllib.parse.urlencode(params)}"

    print(f"\nAbrindo navegador para autenticacao...\nURL: {auth_url}")
    webbrowser.open(auth_url)

    # 2. Iniciar servidor local e aguardar o callback
    with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
        print(f"Aguardando callback em {REDIRECT_URI}...")
        # Processa apenas uma requisição (o callback)
        httpd.handle_request()
        
        if hasattr(httpd, 'auth_code'):
            auth_code = httpd.auth_code
            print("\nCodigo de autorizacao recebido com sucesso!")
        else:
            print("\nFalha ao obter o codigo.")
            return

    # 3. Trocar o Authorization Code pelo Refresh Token
    print("Trocando codigo por tokens...")
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(config['token_endpoint'], data=encoded_data)
    
    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read()
            tokens = json.loads(response_body)
            
            print("\n" + "="*60)
            print("SUCESSO! Aqui estao seus tokens:")
            print("="*60)
            print(f"\nREFRESH_TOKEN (Guarde este valor no seu script):\n{tokens.get('refresh_token')}")
            print("\n" + "-"*60)
            print(f"Access Token (Valido por 1h):\n{tokens.get('access_token')}")
            print("="*60)
            
            if not tokens.get('refresh_token'):
                print("\nATENCAO: Nenhum refresh_token foi retornado. Verifique se voce ja autorizou o app anteriormente ou se os escopos estao corretos.")

    except urllib.error.HTTPError as e:
        print(f"\nErro na troca de tokens: {e}")
        print(e.read().decode())

if __name__ == "__main__":
    main()