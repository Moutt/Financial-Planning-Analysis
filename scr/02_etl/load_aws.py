import boto3
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, ClientError

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do seu Data Lake
nome_arquivo_processado = 'df_consolidade.csv'
NOME_BUCKET = 'balde-alura' 
PREFIXO_S3 = 'bronze/'
PROCESSED_DIR = 'data/processed/'

# Inicializa o cliente do S3 puxando explicitamente do .env
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

print("\nIniciando upload para o Amazon S3...")

caminho_local = os.path.join(PROCESSED_DIR, nome_arquivo_processado)
caminho_s3 = f"{PREFIXO_S3}{nome_arquivo_processado}"

try:
    print(f"Enviando {nome_arquivo_processado}...")
    s3_client.upload_file(caminho_local, NOME_BUCKET, caminho_s3)
    print(f"[SUCESSO] {nome_arquivo_processado} enviado com sucesso!")
    
except NoCredentialsError:
    print("[ERRO] Credenciais da AWS não encontradas no arquivo .env.")
except ClientError as e:
    # Captura erros como "Bucket não existe" ou "Acesso negado"
    print(f"[ERRO AWS] Ocorreu um erro na AWS: {e}")
except Exception as e:
    print(f"[ERRO] Erro inesperado ao enviar {nome_arquivo_processado}: {e}")

print("Processo de ingestão finalizado.")