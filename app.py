from flask import Flask, render_template, request, redirect, url_for
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText # Importar para usar em casos de erro
from email import encoders
import os 
from socket import gaierror, timeout # Importa timeout específico
from urllib.parse import urlparse # Para garantir segurança ao obter dados

app = Flask(__name__)

# --- Configurações de E-mail (Lendo Variáveis de Ambiente) ---
SMTP_SERVER = 'smtp.gmail.com' 
SMTP_PORT = 465 # PORTA ALTERNATIVA PARA SSL/TLS IMPLÍCITO
SENDER_EMAIL = os.environ.get('SMTP_EMAIL')      
SENDER_PASSWORD = os.environ.get('SMTP_PASSWORD') 
RECEIVER_EMAIL = 'matheusroraima2007@gmail.com' 
# -----------------------------

# --- Configurações de Validação de Arquivos ---
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024 
# -----------------------------

def allowed_file(filename):
    """Verifica se a extensão do arquivo está na lista de permitidas."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ROTA 1: Rota Inicial (GET)
@app.route('/')
def index():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
         return render_template('upload.html',
                               message='❌ Erro de Configuração: Credenciais de envio não encontradas no servidor (variáveis de ambiente vazias).',
                               message_type='error')
    return render_template('upload.html') 

# ROTA 2: Rota de Sucesso (GET) - Padrão PRG
@app.route('/success')
def success():
    return render_template('upload.html', 
                           message='✅ Pedido de impressão enviado com sucesso! Verifique seu e-mail.',
                           message_type='success')


# ROTA 3: Rota que recebe os dados do formulário (POST)
@app.route('/upload', methods=['POST'])
def upload_file():
    # Sanitização: O Flask já faz um bom trabalho, mas é bom garantir
    nome_cliente = request.form.get('nome', '').strip()
    email_cliente = request.form.get('email_cliente', '').strip() 
    arquivos = request.files.getlist('arquivo') 
    
    if not arquivos or not nome_cliente or not email_cliente:
        return render_template('upload.html',
                               message='❌ Erro: Por favor, preencha o nome, o e-mail e anexe ao menos um arquivo.',
                               message_type='error'), 400

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"NOVO PEDIDO DE IMPRESSÃO de: {nome_cliente} ({email_cliente})"
    msg.add_header('Reply-To', email_cliente) 
    
    try:
        files_attached = False
        
        # 1. Anexar Arquivos
        for arquivo in arquivos:
            filename = arquivo.filename
            
            if not allowed_file(filename):
                return render_template('upload.html',
                                       message=f'❌ Erro: O arquivo "{filename}" não é um tipo permitido.',
                                       message_type='error'), 400
            
            arquivo.seek(0)
            arquivo_content = arquivo.read()
            
            if len(arquivo_content) > MAX_FILE_SIZE:
                 return render_template('upload.html',
                                       message=f'❌ Erro: O arquivo "{filename}" excede o tamanho máximo de 10MB.',
                                       message_type='error'), 400
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(arquivo_content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
            files_attached = True
            
        if not files_attached:
            return render_template('upload.html',
                                   message='❌ Erro: Nenhum arquivo válido foi anexado.',
                                   message_type='error'), 400
        
        # Adicionar o corpo do e-mail
        body = f"Novo pedido de impressão recebido.\n\nDetalhes do Cliente:\nNome: {nome_cliente}\nE-mail: {email_cliente}\n\nArquivos anexados para impressão."
        msg.attach(MIMEText(body, 'plain'))

        # 2. Bloco de Envio SMTP (Usando SMTP_SSL para a porta 465)
        # O timeout de 15 segundos evita o timeout do Gunicorn
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15) as server: 
            # Não precisa de server.starttls() com SMTP_SSL na porta 465
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        # SUCESSO
        return redirect(url_for('success'))

    # Tratamento de erro específico para SMTP (Autenticação/Senha)
    except smtplib.SMTPAuthenticationError as auth_e:
        print(f"ERRO DE AUTENTICAÇÃO SMTP: {auth_e}")
        return render_template('upload.html',
                               message='❌ Falha na Autenticação SMTP. Verifique sua Senha de Aplicativo no Render (SMTP_PASSWORD).',
                               message_type='error'), 500

    # Tratamento de erro de conexão (Timeout ou Servidor não encontrado)
    except (gaierror, timeout, smtplib.SMTPServerDisconnected) as conn_e:
        print(f"ERRO DE CONEXÃO/TIMEOUT: {conn_e}")
        return render_template('upload.html',
                               message='❌ Erro de Conexão: O servidor de e-mail não respondeu ou a conexão foi bloqueada. (Tente novamente mais tarde)',
                               message_type='error'), 500

    # Tratamento de erro genérico 
    except Exception as e:
        print(f"Erro inesperado ao processar o pedido: {e}")
        return render_template('upload.html',
                               message='❌ Ocorreu um erro inesperado no servidor. O envio falhou. (Erro: Consulte os Logs do Render)',
                               message_type='error'), 500


