import logging
import os
import pathlib
import re
import shutil
import subprocess
from datetime import datetime

import distro
import utils
from dto.info_config_dto import InfoConfigDTO
from dto.servidor_dto import ServidorDTO
from dto.vhost_dto import VhostDTO

path_apache_config_files = ''
path_certificados = ''


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


def listar_vhosts_apache():
    lista_caminho_vhost = []
    proc = subprocess.check_output(['sudo', '/usr/sbin/apachectl', '-D', 'DUMP_VHOSTS'], encoding='UTF-8')
    nomes_arquivos = utils.listar_path_arquivos_diretorio(path_apache_config_files, "*.conf")
    for nome in nomes_arquivos:
        if nome in proc:
            lista_caminho_vhost.append(nome)
    return lista_caminho_vhost


def verificar_configuracao_apache():
    resultado = subprocess.run(['sudo', '/usr/sbin/apachectl', '-t'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Erro
    if resultado.returncode:
        logging.error(resultado.stderr)
        logging.error("Exceção Capturada", exc_info=True)
        info_config = InfoConfigDTO("Erro", resultado.stderr)
    else:
        if utils.is_not_blank(resultado.stdout):
            info_config = InfoConfigDTO("OK", resultado.stdout)
        else:
            info_config = InfoConfigDTO("OK", resultado.stderr)
    return info_config


def obter_informacoes_vhosts_apache():
    # Verifica a configuração do Apache
    info_config = verificar_configuracao_apache()
    vhosts = []
    if info_config.status == 'OK':
        # Listar VHosts Apache
        lista_arquivos_conf = listar_vhosts_apache()
        certificado_dto = None
        for arquivo in lista_arquivos_conf:
            dicionarios = ler_arquivo_conf_apache(arquivo)
            for dicionario in dicionarios:
                if 'VirtualHost' in dicionario:
                    port = dicionario['VirtualHost']
                    numeric_filter = filter(str.isdigit, port)
                    numeric_string = "".join(numeric_filter)
                    port = numeric_string
                else:
                    port = None
                if 'ServerAdmin' in dicionario:
                    server_admin = dicionario['ServerAdmin']
                else:
                    server_admin = None
                if 'ServerName' in dicionario:
                    server_name = dicionario['ServerName']
                else:
                    server_name = None
                if 'ServerAlias' in dicionario:
                    server_alias = dicionario['ServerAlias']
                else:
                    server_alias = None
                if 'SSLCertificateFile' in dicionario:
                    ssl_certificate_file = dicionario['SSLCertificateFile']
                    certificado_dto = utils.ler_certificado_crt(ssl_certificate_file)
                else:
                    ssl_certificate_file = None
                if 'SSLCertificateKeyFile' in dicionario:
                    ssl_certificate_key_file = dicionario['SSLCertificateKeyFile']
                else:
                    ssl_certificate_key_file = None
                if 'SSLCertificateChainFile' in dicionario:
                    ssl_certificate_chain_file = dicionario['SSLCertificateChainFile']
                else:
                    ssl_certificate_chain_file = None

                if certificado_dto is not None:
                    vhost = VhostDTO(info_config, port, server_admin, server_name, server_alias,
                                     ssl_certificate_file, ssl_certificate_key_file, ssl_certificate_chain_file,
                                     arquivo, certificado_dto.__dict__)
                else:
                    vhost = VhostDTO(info_config, port, server_admin, server_name, server_alias,
                                     ssl_certificate_file, ssl_certificate_key_file, ssl_certificate_chain_file,
                                     arquivo)

                vhosts.append(vhost)

        return vhosts

    else:
        vhost = VhostDTO(info_config)
        vhosts.append(vhost)
        return vhosts


def listar_certificados():
    certificados = []
    vhosts = obter_informacoes_vhosts_apache()
    for vhost in vhosts:
        if vhost.infoConfig.status != 'Erro':
            certificados.append(vhost.certificado)
    return certificados


def obter_informacoes():
    nome = ''
    versao = ''
    saida = subprocess.check_output(['sudo', '/usr/sbin/apachectl', '-v'], encoding='UTF-8')
    linhas = saida.splitlines()
    for linha in linhas:
        if "version" in linha:
            stripped1 = linha.split(':', 1)[1]
            stripped2 = stripped1.split('/', 1)
            nome = stripped2[0].replace(" ", "")
            versao = stripped2[1]
    utils.set_log_info("Servidor: " + nome + " Versao: " + versao)
    # Verifica a configuração do Apache
    info_config = verificar_configuracao_apache()
    if info_config.status == 'OK':
        servidor = ServidorDTO(nome, versao, info_config.__dict__, listar_certificados())
    else:
        servidor = ServidorDTO(nome, versao, info_config.__dict__)
    return servidor


def ler_arquivo_conf_apache(caminho_arquivo):
    dicionarios = []
    arquivo = pathlib.Path(caminho_arquivo).read_text()

    vhosts = re.split(r's+(?=<VirtualHost)(.*)((?=<VirtualHost)(?!</VirtualHost>))', arquivo)
    vhosts = [i for i in vhosts if i]

    for vhost in vhosts:
        linhas_vhost = vhost.splitlines()
        linhas_vhost = [vhost.rstrip().lstrip() for vhost in linhas_vhost]
        linhas_vhost = [i for i in linhas_vhost if i and not i.startswith("#")]
        linhas_vhost = [i.strip() for i in linhas_vhost]

        dicionario = {}
        # Filtra apenas os vhosts que tem SSL ativo
        if 'SSLEngine on' in linhas_vhost:
            for linha in linhas_vhost:
                if "<VirtualHost" in linha:
                    dicionario["VirtualHost"] = linha.strip()
                if "ServerName" in linha:
                    dicionario["ServerName"] = linha.strip().split()[1]
                if "ServerAdmin" in linha:
                    dicionario["ServerAdmin"] = linha.strip().split()[1]
                if "ServerAlias" in linha:
                    dicionario["ServerAlias"] = linha.strip().split()[1]
                if "SSLCertificateFile" in linha:
                    dicionario["SSLCertificateFile"] = linha.strip().split()[1]
                if "SSLCertificateKeyFile" in linha:
                    dicionario["SSLCertificateKeyFile"] = linha.strip().split()[1]
                if "SSLCertificateChainFile" in linha:
                    dicionario["SSLCertificateChainFile"] = linha.strip().split()[1]
            dicionarios.append(dicionario)

    return dicionarios


def reiniciar_apache():
    resultado = subprocess.run(['sudo', '/usr/sbin/apachectl', '-k', 'restart'], capture_output=True, text=True)
    if ("Syntax OK" in resultado.stdout) or ("Syntax OK" in resultado.stderr):
        return True
    return False


def reload_apache():
    # CentOS/RHEL/Fedora Linux
    # resultado = subprocess.run(['sudo', 'systemctl', 'reload', 'httpd'], capture_output=True, text=True)
    # Debian/Ubuntu Linux
    resultado = subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Erro
    if resultado.returncode:
        logging.error(resultado.stderr)
        logging.error("Exceção Capturada", exc_info=True)
        info_config = InfoConfigDTO("Erro", resultado.stderr)
    else:
        return True

    return False


def atualizar_arquivos_apache(caminho_arquivo_conf, nome_arquivo_crt, nome_arquivo_key):
    # Cria pasta de backup para os arquivos de configuração apache
    pasta_temp_config_apache = utils.criar_pasta(datetime.now().strftime("%d-%m-%Y"), path_apache_config_files)
    # Copia o arquivo de configuração VirtualHosts para uma pasta de backup
    shutil.copy2(caminho_arquivo_conf, pasta_temp_config_apache)
    utils.set_log_info(
        "Criado backup local do arquivo " + caminho_arquivo_conf + " em " + str(pasta_temp_config_apache))
    # Altera o arquivo de configuração VirtualHosts com o caminho dos novos certificados
    utils.editar_arquivo_conf(caminho_arquivo_conf, "SSLCertificateFile", nome_arquivo_crt)
    utils.editar_arquivo_conf(caminho_arquivo_conf, "SSLCertificateKeyFile", nome_arquivo_key)
    utils.set_log_info("Arquivo " + caminho_arquivo_conf + " alterado")


def listar_certificados_crt():
    utils.set_log_info("Buscando Certificados em: " + path_certificados)

    lista_certificados = []
    for file in utils.listar_path_arquivos_diretorio(path_certificados, "*.crt"):
        cert_file = os.path.join(path_certificados, file)
        certificado_dto = utils.ler_certificado_crt(cert_file)
        utils.set_log_info("Common Name: " + certificado_dto.nomeCompleto + " Data Emissão: " +
                           certificado_dto.dataEmissao + " Data Vencimento: " +
                           certificado_dto.dataVencimento)

        lista_certificados.append(certificado_dto.__dict__)

    if len(lista_certificados) == 0:
        utils.set_log_warning("Nenhum certificado encontrado")

    return lista_certificados


data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
configurar_paths(distro.name())
