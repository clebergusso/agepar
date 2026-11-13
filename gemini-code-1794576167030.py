from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests

# URL específica de Leis e Atos da Agepar
URL_ALVO = "https://www.agepar.pr.gov.br/Pagina/Leis-e-Atos-3"
EMAIL_DESTINO = "cleber.gandrade@agepar.pr.gov.br"

# Configurações do Servidor de E-mail (Variáveis de ambiente do GitHub Secrets)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # Seu e-mail remetente
SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)  # Sua senha de aplicativo do e-mail


def enviar_email(assunto, corpo_texto):
  if not SMTP_USER or not SMTP_PASSWORD:
    print(
        "Credenciais de e-mail não configuradas. Exibindo relatório no"
        " console:"
    )
    print(corpo_texto)
    return

  msg = MIMEMultipart()
  msg["From"] = SMTP_USER
  msg["To"] = EMAIL_DESTINO
  msg["Subject"] = assunto

  msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))

  try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
      servidor.starttls()
      servidor.login(SMTP_USER, SMTP_PASSWORD)
      servidor.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())
    print(f"Relatório enviado com sucesso para {EMAIL_DESTINO}!")
  except Exception as e:
    print(f"Erro ao enviar e-mail: {e}")


def coletar_pagina():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    resposta = requests.get(URL_ALVO, headers=headers, timeout=15)
    resposta.raise_for_status()
    return resposta.text
  except Exception as e:
    print(f"Erro ao acessar a página da Agepar: {e}")
    return None


def analisar_conteudo(html):
  soup = BeautifulSoup(html, "html.parser")
  itens_encontrados = []

  # Varre elementos da página de leis e atos para extrair títulos e links de documentos
  for item in soup.find_all(["a", "h3", "h4", "li"], limit=50):
    texto = item.get_text().strip()
    link = item.get("href") if item.name == "a" else None

    # Filtro focado em atos normativos
    palavras_chave = [
        "portaria",
        "decreto",
        "lei",
        "norma",
        "resolução",
        "deliberação",
    ]
    if any(termo in texto.lower() for termo in palavras_chave) and len(texto) > 10:
      itens_encontrados.append({"titulo": texto, "link": link})

  return itens_encontrados


def gerar_relatorio(itens):
  data_hoje = datetime.now().strftime("%d/%m/%Y")
  assunto = f"Relatório Diário de Atos - Agepar ({data_hoje})"

  corpo = f"RELATÓRIO DIÁRIO DE ATOS - AGEPAR\n"
  corpo += f"Página Monitorada: {URL_ALVO}\n"
  corpo += f"Data da Verificação: {data_hoje}\n\n"
  corpo += "-" * 50 + "\n\n"

  if not itens:
    corpo += (
        "Nenhuma nova norma ou ato oficial identificado na varredura de hoje."
    )
  else:
    for i, ato in enumerate(itens, 1):
      corpo += f"{i}. {ato['titulo']}\n"
      if ato["link"]:
        link_completo = (
            ato["link"]
            if ato["link"].startswith("http")
            else f"https://www.agepar.pr.gov.br{ato['link']}"
        )
        corpo += f"   Link: {link_completo}\n"
      corpo += "-" * 30 + "\n"

  enviar_email(assunto, corpo)


if __name__ == "__main__":
  html_pagina = coletar_pagina()
  if html_pagina:
    atos = analisar_conteudo(html_pagina)
    gerar_relatorio(atos)