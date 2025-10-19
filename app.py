from flask import Flask, render_template, request, redirect, url_for # 🎯 Importados redirect e url_for
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

app = Flask(__name__)

# --- Configurações de E-mail (Mantenha as suas configurações reais aqui) ---
SMTP_SERVER = 'smtp.gmail.com' 
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('SMTP_EMAIL')
SENDER_PASSWORD = os.environ.get('SMTP_PASSWORD') # Use senhas de aplicativo se for Gmail/Outlook!
RECEIVER_EMAIL = 'matheusroraima2007@gmail.com'
# -----------------------------

# ROTA 1: Rota Inicial (a página de formulário)
@app.route('/')
def index():
    # Carrega a página inicial, sem mensagens
    return render_template('upload.html') 

# ROTA 2: Rota de Sucesso (GET) - NOVA ROTA
# Destino seguro após o envio bem-sucedido. Previne o reenvio (PRG).
@app.route('/success')
def success():
    return render_template('upload.html', 
                           message='✅ Pedido de impressão enviado com sucesso! Verifique seu e-mail.',
                           message_type='success')


# ROTA 3: Rota que recebe os dados do formulário e envia o e-mail
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        nome_cliente = request.form['nome']
        arquivos = request.files.getlist('arquivo') 
        
        # 🎯 AJUSTE DE LÓGICA 1: Trata erro de campos faltando e retorna ao formulário
        if not arquivos or not nome_cliente:
            return render_template('upload.html',
                                   message='❌ Erro: Nome ou arquivos faltando. Por favor, preencha todos os campos.',
                                   message_type='error'), 400

        # O restante do código de envio de e-mail:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"NOVO PEDIDO DE IMPRESSÃO de: {nome_cliente}"
        
        for arquivo in arquivos:
            arquivo_content = arquivo.read()
            if not arquivo_content:
                continue

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(arquivo_content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{arquivo.filename}"')
            msg.attach(part)
            
        # Bloco de Envio
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        # 🎯 AJUSTE DE LÓGICA 2: Se o envio for um sucesso, REDIRECIONE para a rota /success
        return redirect(url_for('success'))

    except Exception as e:
        print(f"Erro ao processar o pedido: {e}")
        # Retorna uma mensagem de erro amigável ao cliente (em caso de falha de conexão/SMTP)
        return render_template('upload.html',
                               message='❌ Ocorreu um erro inesperado. Falha no envio do e-mail. Tente novamente.',
                               message_type='error')


if __name__ == '__main__':
    # Roda o servidor web (você verá no seu navegador em http://127.0.0.1:5000/)
    app.run(debug=True)
