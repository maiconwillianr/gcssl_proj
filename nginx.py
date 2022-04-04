import logging
import re
import subprocess

import utils
from dto.info_config_dto import InfoConfigDTO
from dto.servidor_dto import ServidorDTO
from dto.vhost_dto import VhostDTO

path_nginx_config_files = "/etc/nginx"


def set_log_info(log_info):
    logging.info(log_info)


# ^(?!\s*#).*?$ - tira linhas com comentarios
def ler_arquivo_conf_nginx(caminho_arquivo):
    dicionarios = []

    with open(caminho_arquivo, 'r') as f:
        conteudo = f.read()

        # remove as linhas comentadas
        conteudo = re.findall(r'^(?!\s*#).*?$', conteudo, re.MULTILINE)
        conteudo = "\n".join(conteudo)
        if 'ssl_certificate' in conteudo:
            # busca blocos de server
            vhosts = re.findall(r'^\s*(server\s*)({.*?)((}\s.*?(?=^server))|(}\s.*?})|(}\s.*?(?!^server)\s*))',
                                conteudo, flags=re.DOTALL | re.MULTILINE)
            if vhosts:
                for vhost in vhosts:
                    if any('ssl_certificate' in value for value in vhost):
                        dicionario = {}
                        vhost = "\n".join(vhost)
                        vhost = vhost.splitlines()
                        for linhas_vhost in vhost:
                            linha = linhas_vhost.rstrip().lstrip()
                            linha = linha.replace(";", "")
                            linha = linha.split()
                            if "server_name" in linha:
                                dicionario["server_name"] = linha[1].replace(";", "")
                            if "ssl_certificate" in linha:
                                dicionario["ssl_certificate"] = linha[1].replace(";", "")
                            if "ssl_certificate_key" in linha:
                                dicionario["ssl_certificate_key"] = linha[1].replace(";", "")
                        dicionarios.append(dicionario)

    return dicionarios


def listar_arquivos_conf_nginx():
    path_arquivos = utils.listar_path_arquivos_diretorio(path_nginx_config_files, "*.conf")
    return path_arquivos


def obter_informacoes_vhosts_nginx():
    # Verifica a configuração do Nginx
    info_config = verificar_configuracao_nginx()
    vhosts = []
    if info_config.status == 'OK':
        # Listar arquivos de configuracao nginx
        lista_arquivos_conf = listar_arquivos_conf_nginx()
        certificado_dto = None

        for arquivo in lista_arquivos_conf:
            dicionarios = ler_arquivo_conf_nginx(arquivo)
            for dicionario in dicionarios:
                if 'port' in dicionario:
                    port = dicionario['port']
                    numeric_filter = filter(str.isdigit, port)
                    numeric_string = "".join(numeric_filter)
                    port = numeric_string
                else:
                    port = None
                if 'server_name' in dicionario:
                    server_name = dicionario['server_name']
                else:
                    server_name = None
                if 'ssl_certificate' in dicionario:
                    ssl_certificate_file = dicionario['ssl_certificate']
                    certificado_dto = utils.ler_certificado_crt(ssl_certificate_file)
                else:
                    ssl_certificate_file = None
                if 'ssl_certificate_key' in dicionario:
                    ssl_certificate_key_file = dicionario['ssl_certificate_key']
                else:
                    ssl_certificate_key_file = None

                # Campos nao existem no Nginx
                server_admin = None
                server_alias = None
                ssl_certificate_chain_file = None
                if certificado_dto is not None:
                    vhost = VhostDTO(info_config, port, server_admin, server_name, server_alias,
                                     ssl_certificate_file, ssl_certificate_key_file, ssl_certificate_chain_file,
                                     arquivo, certificado_dto.__dict__)
                else:
                    vhost = VhostDTO(info_config, port, server_admin, server_name, server_alias,
                                     ssl_certificate_file, ssl_certificate_key_file,
                                     ssl_certificate_chain_file, arquivo)

                vhosts.append(vhost)

        return vhosts

    else:
        vhost = VhostDTO(info_config)
        vhosts.append(vhost)
        return vhosts


def verificar_configuracao_nginx():
    resultado = subprocess.run(['sudo', '/usr/sbin/nginx', '-t'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Erro
    if resultado.returncode:
        logging.error(resultado.stderr)
        logging.error("Exceção Capturada", exc_info=True)
        resultado.stderr = resultado.stderr.replace("\"", "")
        info_config = InfoConfigDTO("Erro", resultado.stderr)
    else:
        if utils.is_not_blank(resultado.stdout):
            info_config = InfoConfigDTO("OK", resultado.stdout)
        else:
            info_config = InfoConfigDTO("OK", resultado.stderr)
    return info_config


def listar_certificados():
    certificados = []
    vhosts = obter_informacoes_vhosts_nginx()
    for vhost in vhosts:
        if 'certificado' in vhost:
            certificados.append(vhost['certificado'])
    return certificados


def obter_informacoes():
    nome = ''
    versao = ''
    resultado = subprocess.run(['/usr/sbin/nginx', '-v'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Erro
    if resultado.returncode:
        logging.error(resultado.stderr)
        logging.error("Exceção Capturada", exc_info=True)
        info_config = InfoConfigDTO("Erro", resultado.stderr)
    else:
        linhas = resultado.stderr.split()
        stripped = linhas[2].split('/', 2)
        nome = stripped[0]
        versao = stripped[1]
    set_log_info("Servidor: " + nome + " Versao: " + versao)
    # Verifica a configuração do nginx
    info_config = verificar_configuracao_nginx()
    if info_config.status == 'OK':
        servidor = ServidorDTO(nome, versao, info_config.__dict__, listar_certificados())
    else:
        servidor = ServidorDTO(nome, versao, info_config.__dict__)
    return servidor
