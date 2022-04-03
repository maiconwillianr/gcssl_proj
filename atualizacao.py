# -*- Coding: UTF-8 -*-
# coding: utf-8
import os
import shutil
from datetime import datetime
from pathlib import Path

import ambiente
import apache
import nginx
import utils
from dto.atualizacao_dto import AtualizacaoDTO
from dto.vhost_dto import VhostDTO


def criar_backup(path_completo_crt: str, path_completo_key: str):
    # Cria backup local dos certificados vencidos
    dt = datetime.now().strftime("%d-%m-%Y %H:%M:%S").split()
    pasta_backup_local = utils.criar_pasta(dt[1], utils.criar_pasta("backup_" + dt[0], utils.cwd))
    # Move os certificados para o backup
    utils.mover_arquivo(path_completo_crt, pasta_backup_local)
    utils.mover_arquivo(path_completo_key, pasta_backup_local)
    utils.set_log_info("Criado backup local dos certificados antigos em " + str(pasta_backup_local))


def substituir_arquivos(vhost: VhostDTO,  pathNewCert: str):
    path_completo_crt = vhost.get_ssl_certificate_file()
    path_crt = path_completo_crt
    path_crt_index = path_crt.rindex("/")
    path_crt = path_crt[:path_crt_index]
    path_completo_key = vhost.get_ssl_certificate_key_file()
    path_key = path_completo_key
    path_key_index = path_key.rindex("/")
    path_key = path_key[:path_key_index]
    # Cria pasta temporaria para o download dos novos certificados
    pasta_destino_temp = utils.criar_pasta("temp_" + datetime.now().strftime("%d-%m-%Y"), utils.cwd)
    # Extrai arquivo com os certificados
    utils.extract(pathNewCert, pasta_destino_temp)
    list_arquivos = os.listdir(pasta_destino_temp)
    for arquivo in list_arquivos:
        file_extension = Path(arquivo).suffix
        if file_extension == '.crt':
            nome_arquivo_crt = Path(arquivo)
        elif file_extension == '.key':
            nome_arquivo_key = Path(arquivo)

    # Obtem o caminho para o novo arquivo .crt
    caminho_temp_novo_crt = os.path.join(pasta_destino_temp, nome_arquivo_crt)
    # Renomeia o arquivo recebido
    nome_crt_original = os.path.basename(vhost.get_ssl_certificate_file())
    os.rename(caminho_temp_novo_crt, str(Path(pasta_destino_temp, nome_crt_original)))
    caminho_temp_novo_crt = str(Path(pasta_destino_temp, nome_crt_original))
    # verificar se o arquivo cert foi baixado e a validade (precisa implementar)
    # Obtem o caminho para o novo arquivo .key
    caminho_temp_novo_key = os.path.join(pasta_destino_temp, nome_arquivo_key)
    # Renomeia o arquivo recebido via ssh
    nome_key_original = os.path.basename(vhost.get_ssl_certificate_key_file())
    os.rename(caminho_temp_novo_key, str(Path(pasta_destino_temp, nome_key_original)))
    caminho_temp_novo_key = str(Path(pasta_destino_temp, nome_key_original))
    # Verifica se os arquivos baixados .crt e .key correspondem
    compativeis = utils.comparar_certificado(caminho_temp_novo_crt, caminho_temp_novo_key)
    if compativeis:
        utils.set_log_info("Certificados compativeis")
        # Cria backup local dos certificados vencidos
        criar_backup(path_completo_crt, path_completo_key)
        # Move os novos certificados da pasta temporaria para a pasta de certificados do apache
        utils.mover_arquivo(caminho_temp_novo_crt, path_crt)
        utils.mover_arquivo(caminho_temp_novo_key, path_key)
        # Remove a pasta temporaria de download
        shutil.rmtree(pasta_destino_temp)


def atualizar_certificado(commonName: str, pathNewCert: str):

    utils.set_log_info("Executando script atualizacao.py")

    try:

        vhosts = apache.obter_informacoes_vhosts_apache()

        for vhost in vhosts:
            cert = vhost.get_certificado()
            if cert['nomeCompleto'] == commonName:
                path_completo_crt = vhost.get_ssl_certificate_file()
                certificado_anterior = utils.ler_certificado_crt(path_completo_crt)
                substituir_arquivos(vhost, pathNewCert)
                # Verifica se a configuração possui erros
                retorno_configuracao = apache.verificar_configuracao_apache()
                if retorno_configuracao:
                    utils.set_log_info("Certificado atualizado com Sucesso")
                else:
                    utils.set_log_info("Apache com erro de configuração")

                apache.reload_apache()
                utils.set_log_info("Certificados atualizados com Sucesso")

                # Cria um envio
                file = open(utils.obter_log())
                log = file.read()
                file.close()

                certificado_atual = utils.ler_certificado_crt(path_completo_crt)

                envio_atualizacao = AtualizacaoDTO(ambiente.obter_host_name(), utils.obter_token_local(),
                                                   ambiente.get_ip(), certificado_anterior.__dict__,
                                                   certificado_atual.__dict__,
                                                   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                   datetime.now().strftime("%d/%m/%Y %H:%M:%S"), log)
                # Converte para JSON
                parsed_json = utils.converter_json(envio_atualizacao.__dict__)
                return parsed_json

    except Exception as err:
        utils.set_log_error("Exceção Capturada", exc_info=True)
        utils.set_log_error(err)


def atualizar_certificado2(commonName: str, pathNewCert: str):
    utils.set_log_info("Executando script atualizacao.py servidor nginx")

    try:

        # ler todos os certificados configurados no host
        vhosts = []
        if os.path.exists('/etc/nginx'):
            vhosts.append(nginx.obter_informacoes_vhosts_nginx())
        if os.path.exists('/etc/apache2'):
            vhosts.append(apache.obter_informacoes_vhosts_apache())

        # filtrar certificados que devem ser atualizados
        for vhost in vhosts:
            cert = vhost['certificado']
            if cert['nomeCompleto'] == commonName:
                path_completo_crt = vhost['sslcertificateFile']
                certificado_anterior = utils.ler_certificado_crt(path_completo_crt)
                path_crt = path_completo_crt
                path_crt_index = path_crt.rindex("/")
                path_crt = path_crt[:path_crt_index]
                path_completo_key = vhost['sslcertificateKeyFile']
                path_key = path_completo_key
                path_key_index = path_key.rindex("/")
                path_key = path_key[:path_key_index]
                # Cria pasta temporaria para o download dos novos certificados
                pasta_destino_temp = utils.criar_pasta("temp_" + datetime.now().strftime("%d-%m-%Y"), utils.cwd)
                # Extrai arquivo com os certificados
                utils.extract(pathNewCert, pasta_destino_temp)
                list_arquivos = os.listdir(pasta_destino_temp)
                for arquivo in list_arquivos:
                    file_extension = Path(arquivo).suffix
                    if file_extension == '.crt':
                        nome_arquivo_crt = Path(arquivo)
                    elif file_extension == '.key':
                        nome_arquivo_key = Path(arquivo)

                # Obtem o caminho para o novo arquivo .crt
                caminho_temp_novo_crt = os.path.join(pasta_destino_temp, nome_arquivo_crt)
                # Renomeia o arquivo recebido
                nome_crt_original = os.path.basename(vhost['sslcertificateFile'])
                os.rename(caminho_temp_novo_crt, str(Path(pasta_destino_temp, nome_crt_original)))
                caminho_temp_novo_crt = str(Path(pasta_destino_temp, nome_crt_original))
                # verificar se o arquivo cert foi baixado e a validade (precisa implementar)
                # Obtem o caminho para o novo arquivo .key
                caminho_temp_novo_key = os.path.join(pasta_destino_temp, nome_arquivo_key)
                # Renomeia o arquivo recebido via webservices
                nome_key_original = os.path.basename(vhost['sslcertificateKeyFile'])
                os.rename(caminho_temp_novo_key, str(Path(pasta_destino_temp, nome_key_original)))
                caminho_temp_novo_key = str(Path(pasta_destino_temp, nome_key_original))
                # Verifica se os arquivos baixados .crt e .key correspondem
                compativeis = utils.comparar_certificado(caminho_temp_novo_crt, caminho_temp_novo_key)
                if compativeis:
                    utils.set_log_info("Certificados compativeis")
                    # Cria backup local dos certificados vencidos
                    dt = datetime.now().strftime("%d-%m-%Y %H:%M:%S").split()
                    pasta_backup_local = utils.criar_pasta(dt[1], utils.criar_pasta("backup_" + dt[0], utils.cwd))
                    # Move os certificados para o backup
                    utils.mover_arquivo(path_completo_crt, pasta_backup_local)
                    utils.mover_arquivo(path_completo_key, pasta_backup_local)
                    utils.set_log_info("Criado backup local dos certificados antigos em " + str(pasta_backup_local))
                    # Move os novos certificados da pasta temporaria para a pasta de certificados do apache
                    utils.mover_arquivo(caminho_temp_novo_crt, path_crt)
                    utils.mover_arquivo(caminho_temp_novo_key, path_key)
                    # Remove a pasta temporaria de download
                    shutil.rmtree(pasta_destino_temp)
                    # Verifica se a configuração possui erros
                    retorno_configuracao = apache.verificar_configuracao_apache()
                    if retorno_configuracao:
                        utils.set_log_info("Certificado atualizado com Sucesso")
                    else:
                        utils.set_log_info("Apache com erro de configuração")

                    apache.reload_apache()
                    utils.set_log_info("Certificados atualizados com Sucesso")

                    # Cria um envio
                    file = open(utils.obter_log())
                    log = file.read()
                    file.close()

                    certificado_atual = apache.ler_certificado_crt(path_completo_crt)

                    envio_atualizacao = AtualizacaoDTO(ambiente.obter_host_name(), utils.obter_token_local(),
                                                       ambiente.get_ip(), certificado_anterior.__dict__,
                                                       certificado_atual.__dict__,
                                                       datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                       datetime.now().strftime("%d/%m/%Y %H:%M:%S"), log)
                    # Converte para JSON
                    parsed_json = utils.converter_json(envio_atualizacao.__dict__)
                    return parsed_json

    except Exception as err:
        utils.set_log_error("Exceção Capturada", exc_info=True)
        utils.set_log_error(err)
