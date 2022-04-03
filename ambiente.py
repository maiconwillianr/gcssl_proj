import logging
import os
import platform
import socket
import subprocess

import apache
import nginx
import utils
from dto.sistema_operacional_dto import SistemaOperacionalDTO


class HostDTO:
    def __init__(self, nome, ip, python, sistema, servidores):
        self.nome = nome
        self.ip = ip
        self.python = python
        self.sistemaOperacional = sistema
        self.servidores = servidores


def set_log_info(log_info):
    logging.info(log_info)


def configurar_paths(nome_sistema):
    global path_apache_config_files
    global path_certificados
    if "Ubuntu" in nome_sistema:
        path_apache_config_files = '/etc/apache2/sites-enabled/'
        path_certificados = '/home/maiconribeiro/Desenvolvimento/'
    elif "openSUSE" in nome_sistema:
        path_apache_config_files = '/etc/apache2/vhosts.d/'
        path_certificados = '/etc/apache2/ssl.crt'
    elif "SLES" in nome_sistema:
        path_apache_config_files = '/etc/apache2/vhosts.d/'
        path_certificados = '/etc/apache2/ssl.crt'


def obter_informacoes_host_json():
    servidores = []
    if os.path.exists('/etc/nginx'):
        servidores.append(nginx.obter_informacoes().__dict__)
    if os.path.exists('/etc/apache2'):
        servidores.append(apache.obter_informacoes().__dict__)
    host = HostDTO(obter_host_name(), get_ip(), obter_versao_python(),
                   obter_info_sistema_operacional().__dict__, servidores)
    return utils.converter_json(host.__dict__)


def obter_local_instalacao():
    return os.getcwd()


def obter_versao_python():
    return platform.python_version()


def obter_host_name():
    return socket.gethostname()


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def obter_informacoes_sistema_operacional():
    # dictionary
    info = {}
    # platform details
    platform_details = platform.platform()
    # adding it to dictionary
    info["platform details"] = platform_details
    # system name
    system_name = platform.system()
    # adding it to dictionary
    info["system name"] = system_name
    # processor name
    processor_name = platform.processor()
    # adding it to dictionary
    info["processor name"] = processor_name
    # architectural detail
    architecture_details = platform.architecture()
    # adding it to dictionary
    info["architectural detail"] = architecture_details
    # printing the details
    for i, j in info.items():
        print(i, " - ", j)


def obter_info_sistema_operacional():
    nome = ''
    versao = ''
    descricao = ''
    saida = subprocess.check_output(['cat', '/etc/os-release'], encoding='UTF-8')
    linhas = saida.splitlines()
    for linha in linhas:
        if linha.startswith("NAME"):
            stripped = linha.split('=', 1)[1]
            nome = stripped.strip().replace('"', "")
        elif "VERSION_ID" in linha:
            stripped = linha.split('=', 1)[1]
            versao = stripped.strip().replace('"', "")
        elif "PRETTY_NAME" in linha:
            stripped = linha.split('=', 1)[1]
            descricao = stripped.strip().replace('"', "")
    set_log_info("Sistema: " + nome + " Versao: " + versao)
    try:
        return SistemaOperacionalDTO(nome, versao, descricao)
    except RuntimeError as runex:
        logging.error(runex)
        logging.error("Exceção Capturada", exc_info=True)
        raise RuntimeError


sistema_operacional = obter_info_sistema_operacional()
apache.configurar_paths(sistema_operacional.nome)
