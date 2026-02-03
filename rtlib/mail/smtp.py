import smtplib
import ssl
import base64
import json
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_oauth_token_from_refresh_token(token_endpoint, client_id, client_secret, refresh_token):
    #Obtém um novo access_token usando um refresh_token existente.
    #Endpoints comuns:
    #- Google: https://oauth2.googleapis.com/token
    #- Microsoft: https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(token_endpoint, data=encoded_data)
    
    with urllib.request.urlopen(req) as response:
        response_body = response.read()
        return json.loads(response_body)['access_token']

def send_tls_email(smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, smtp_rcpt, subject, body, allow_self_signed=False, oauth_token=None, oauth_config=None):
    retorno = ""

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = smtp_rcpt
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    # Se não foi passado um token pronto, mas temos a configuração para buscar um
    if not oauth_token and oauth_config:
        try:
            oauth_token = get_oauth_token_from_refresh_token(
                oauth_config.get('token_endpoint'),
                oauth_config.get('client_id'),
                oauth_config.get('client_secret'),
                oauth_config.get('refresh_token')
            )
        except Exception as e:
            return f"Erro ao obter token OAuth2: {e}"

    # Configura a conexão SMTP
    context = ssl.create_default_context()
    if allow_self_signed:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.ehlo()
            if oauth_token:
                auth_string = f"user={smtp_user}\1auth=Bearer {oauth_token}\1\1"
                auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("ascii")
                code, resp = server.docmd("AUTH", "XOAUTH2 " + auth_b64)
                if code != 235:
                    raise smtplib.SMTPAuthenticationError(code, resp)
            else:
                server.login(smtp_user, smtp_pass)
            retorno = server.sendmail(smtp_from, smtp_rcpt, msg.as_string())
    except smtplib.SMTPException as e:
        retorno = e

    return retorno

def send_ssl_email(smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, smtp_rcpt, subject, body, allow_self_signed=False, oauth_token=None, oauth_config=None):
    retorno = ""

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = smtp_rcpt
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    # Se não foi passado um token pronto, mas temos a configuração para buscar um
    if not oauth_token and oauth_config:
        try:
            oauth_token = get_oauth_token_from_refresh_token(
                oauth_config.get('token_endpoint'),
                oauth_config.get('client_id'),
                oauth_config.get('client_secret'),
                oauth_config.get('refresh_token')
            )
        except Exception as e:
            return f"Erro ao obter token OAuth2: {e}"

    # Configura a conexão SMTP
    context = ssl.create_default_context()
    if allow_self_signed:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.ehlo()
            if oauth_token:
                auth_string = f"user={smtp_user}\1auth=Bearer {oauth_token}\1\1"
                auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("ascii")
                code, resp = server.docmd("AUTH", "XOAUTH2 " + auth_b64)
                if code != 235:
                    raise smtplib.SMTPAuthenticationError(code, resp)
            else:
                server.login(smtp_user, smtp_pass)
            retorno = server.sendmail(smtp_from, smtp_rcpt, msg.as_string())
    except smtplib.SMTPException as e:
        retorno = e

    return retorno