# -*- Coding: UTF-8 -*-
# coding: utf-8
import glob
import hashlib
import json
import logging
import os
import os.path
import pathlib
import re
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import NameOID
from dotenv import load_dotenv

# Get the current working
# directory (CWD)
from dto.certificado_dto import CertificadoDTO

cwd = os.getcwd()
data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def set_log_info(log_info):
    logging.info(log_info)


def set_log_error(log_error):
    logging.error(log_error)


def set_log_warning(log_warning):
    logging.warning(log_warning)


def obter_data_atual_formatada():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def obter_data_atual():
    return datetime.now()


def listar_nomes_arquivos_diretorio(caminho, extensao):
    arquivos = []
    os.chdir(caminho)
    for file in glob.glob(extensao):
        arquivos.append(file)
    return arquivos


def listar_path_arquivos_diretorio(caminho, extensao):
    arquivos = []
    os.chdir(caminho)
    for file in glob.glob(extensao):
        arquivos.append(os.path.join(caminho, file))
    return arquivos


def criar_pasta(nome, caminho):
    try:
        path = Path(caminho, nome)
        if not os.path.exists(path):
            os.system(f"sudo mkdir {str(path.absolute())}")
            os.system(f"sudo chmod 777 {str(path.absolute())}")

        return path

    except OSError as oserror:
        logging.error(oserror)
        logging.error("Exceção Capturada", exc_info=True)


def mover_arquivos(origem, destino):
    nome_arquivos = [i for i in os.listdir(origem) if not os.path.isdir(i)]
    for nome_arquivo in nome_arquivos:
        name, ext = os.path.splitext(nome_arquivo)
        if ext != '.txt':
            shutil.move(os.path.join(origem, nome_arquivo), destino)


def mover_arquivo(nome_arquivo, destino):
    shutil.move(nome_arquivo, destino)


def copiar_arquivo(nome_arquivo, destino):
    shutil.copy(nome_arquivo, destino)


def is_not_blank(s):
    return bool(s and not s.isspace())


def ler_certificado_crt(caminho_certificado):
    certificado_dto = None
    try:
        cert = x509.load_pem_x509_certificate(pathlib.Path(caminho_certificado).read_bytes())
        issued_to = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        issued_by = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        dt_validade = cert.not_valid_after.strftime("%d/%m/%Y %H:%M:%S")
        dt_criacao = cert.not_valid_before.strftime("%d/%m/%Y %H:%M:%S")
        vencido = dt_criacao > dt_validade
        path = caminho_certificado
        path_index = path.rindex("/")
        path = path[:path_index]
        md5 = obter_md5_arquivo_crt(caminho_certificado)
        certificado_dto = CertificadoDTO(issued_to, issued_by, path, md5, dt_criacao, dt_validade, vencido)
    except FileNotFoundError:
        logging.error("Certificado nao encontrado")

    return certificado_dto


def ler_arquivo_conf(caminho_arquivo):
    dicionario = {}
    linhas_arquivo = []
    arquivo = open(caminho_arquivo, "r+")
    try:
        conteudo_arquivo = [x.rstrip("\n") for x in arquivo.readlines()]
        for arg in conteudo_arquivo:
            linhas_arquivo.append(arg.split())

    finally:
        arquivo.close()

    for l in linhas_arquivo:
        if len(l) == 2:
            dicionario[l[0]] = l[1]

    return dicionario


def editar_arquivo_conf(caminho_arquivo, chave, valor):
    dicionario = ler_arquivo_conf(caminho_arquivo)
    try:
        arquivo_entrada = open(caminho_arquivo, "rt")
        data = arquivo_entrada.read()
        data = data.replace(dicionario[chave], valor)
        arquivo_entrada.close()
        arquivo_entrada = open(caminho_arquivo, "wt")
        arquivo_entrada.write(data)
        arquivo_entrada.close()

    finally:
        print(ler_arquivo_conf(caminho_arquivo))


def obter_md5_arquivo_crt(path_arquivo):
    result = subprocess.run(['openssl', 'x509', '-noout', '-modulus', '-in', path_arquivo],
                            check=True, stdout=subprocess.PIPE, universal_newlines=True)
    modulo = (result.stdout.split('=')[-1]).strip()
    hash_object = hashlib.md5(modulo.encode())
    md5_hash = hash_object.hexdigest()
    return md5_hash


def comparar_certificado(cert, key):
    cert = x509.load_pem_x509_certificate(pathlib.Path(cert).read_bytes())
    key = load_pem_private_key(pathlib.Path(key).read_bytes(), password=None)
    cert_pub = cert.public_key().public_bytes(serialization.Encoding.PEM,
                                              format=serialization.PublicFormat.SubjectPublicKeyInfo)
    key_pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    if cert_pub != key_pub:
        return False
    else:
        return True


def criar_bundle(arquivo_crt, cadeias):
    # Certificado principal
    cert = x509.load_pem_x509_certificate(pathlib.Path(arquivo_crt).read_bytes())
    with open(Path(cadeias), 'r') as f:
        conteudo = f.read()
        f.close()
    certs = re.findall(r'(-----BEGIN .+?-----(?s).+?-----END .+?-----)', conteudo, flags=re.DOTALL | re.MULTILINE)
    extensao_novo_arquivo = '.ca-bundle'
    path_novo_arquivo = Path(arquivo_crt).parent.absolute()
    nome_novo_arquivo = Path(arquivo_crt).stem
    path_completo_novo_arquivo = os.path.join(path_novo_arquivo, nome_novo_arquivo + extensao_novo_arquivo)
    with open(path_completo_novo_arquivo, "a+") as f:
        data = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        f.write(data)
        for c in certs:
            f.write(c + '\n')
        f.close()
    return path_completo_novo_arquivo


def converter_json(entidade):
    return json.loads(json.dumps(entidade))


def obter_log():
    return log_path


def criar_env(token):
    load_dotenv()
    path = os.path.join(cwd, '.env')
    f = open(path, 'w+')
    f.write('CLIENT_ID=' + token)
    f.close()
    os.environ["CLIENT_ID"] = token


def obter_token_local():
    load_dotenv()
    return os.environ.get('CLIENT_ID')


def extract(file_name: str, path_destination: str, password=None):
    file_extension = Path(file_name).suffix
    if file_extension == '.tar.gz':
        file = tarfile.open(file_name)
        file.extractall(path_destination)
        file.close()
    elif file_extension == '.zip':
        zf = ZipFile(file_name)
        try:
            zf.testzip()
            # zip sem senha
            with ZipFile(file_name, 'r') as zipObj:
                zipObj.extractall(path_destination)
        except RuntimeError as e:
            if 'encrypted' in str(e):
                # zip com senha
                with ZipFile(file_name, 'r') as zipObj:
                    zipObj.extractall(pwd=bytes(password, 'utf-8'))
            else:
                logging.error("Erro ao descompactar zip")


# Cria pasta para o armazenamento de Logs
criar_pasta("Logs", cwd)
log_path = Path(cwd, "Logs", "log-" + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + ".txt")
# log_path = os.path.join(cwd, "Logs", "log-" + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + ".txt")
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)
