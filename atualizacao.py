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
from dto.item_atualizacao_dto import ItemAtualizacaoDTO
from dto.vhost_dto import VhostDTO


def criar_backup(path_completo_crt: str, path_completo_key: str):
    # Cria backup local dos certificados vencidos
    dt = datetime.now().strftime("%d-%m-%Y %H:%M:%S").split()
    pasta_backup_local = utils.criar_pasta(dt[1], utils.criar_pasta("backup_" + dt[0], utils.cwd))
    # Move os certificados para o backup
    utils.mover_arquivo(path_completo_crt, pasta_backup_local)
    utils.mover_arquivo(path_completo_key, pasta_backup_local)
    utils.set_log_info("Criado backup local dos certificados antigos em " + str(pasta_backup_local))


def atualizar_certificado_nginx(vhost: VhostDTO, pasta_destino_temp: str, path_novo_arquivo_pem: str,
                                path_novo_arquivo_crt: str, path_novo_arquivo_key: str):
    path_completo_crt = vhost.get_ssl_certificate_file()
    path_crt = path_completo_crt
    path_crt_index = path_crt.rindex("/")
    path_crt = path_crt[:path_crt_index]
    path_completo_key = vhost.get_ssl_certificate_key_file()
    path_key = path_completo_key
    path_key_index = path_key.rindex("/")
    path_key = path_key[:path_key_index]
    # Prepara bundle para instalacao no nginx
    if path_novo_arquivo_pem:
        path_novo_arquivo_crt_bundle = utils.criar_bundle(path_novo_arquivo_crt, path_novo_arquivo_pem)
        nome_novo_arquivo_crt_bundle = os.path.basename(path_novo_arquivo_crt_bundle)
    # verificar se o arquivo cert foi baixado e a validade (precisa implementar)
    # Obtem o caminho para o novo arquivo .key
    caminho_temp_novo_key = os.path.join(pasta_destino_temp, path_novo_arquivo_key)
    # Renomeia o arquivo key recebido via ssh
    nome_key_original = os.path.basename(vhost.get_ssl_certificate_key_file())
    os.rename(caminho_temp_novo_key, str(Path(pasta_destino_temp, nome_key_original)))
    caminho_temp_novo_key = str(Path(pasta_destino_temp, nome_key_original))
    # Verifica se os arquivos baixados .crt e .key correspondem
    compativeis = utils.comparar_crt_key(path_novo_arquivo_crt_bundle, caminho_temp_novo_key)
    if compativeis:
        utils.set_log_info("Certificados compativeis")
        # Cria backup local dos certificados vencidos
        criar_backup(path_completo_crt, path_completo_key)
        # Move os novos certificados da pasta temporaria para a pasta de certificados do apache
        utils.copiar_arquivo(path_novo_arquivo_crt_bundle, path_crt)
        utils.copiar_arquivo(caminho_temp_novo_key, path_key)
        # Checa se o arquivo foi copiado
        path_destino_arquivo_crt = os.path.join(path_crt, nome_novo_arquivo_crt_bundle)
        if os.path.exists(path_destino_arquivo_crt):
            # Altera arquivo de configuracao nginx
            valor_arquivo_conf = path_destino_arquivo_crt + ';'
            utils.editar_arquivo_conf(vhost.get_path_file(), 'ssl_certificate', valor_arquivo_conf)


def atualizar_certificado_apache(vhost: VhostDTO, pasta_destino_temp: str, path_novo_arquivo_crt: str,
                                 path_novo_arquivo_key: str):
    path_completo_crt = vhost.get_ssl_certificate_file()
    path_crt = path_completo_crt
    path_crt_index = path_crt.rindex("/")
    path_crt = path_crt[:path_crt_index]
    path_completo_key = vhost.get_ssl_certificate_key_file()
    path_key = path_completo_key
    path_key_index = path_key.rindex("/")
    path_key = path_key[:path_key_index]
    # Obtem o caminho para o novo arquivo .crt
    caminho_temp_novo_crt = os.path.join(pasta_destino_temp, path_novo_arquivo_crt)
    # Renomeia o arquivo recebido
    nome_crt_original = os.path.basename(vhost.get_ssl_certificate_file())
    os.rename(caminho_temp_novo_crt, str(Path(pasta_destino_temp, nome_crt_original)))
    caminho_temp_novo_crt = str(Path(pasta_destino_temp, nome_crt_original))
    # Obtem o caminho para o novo arquivo .key
    caminho_temp_novo_key = os.path.join(pasta_destino_temp, path_novo_arquivo_key)
    # Renomeia o arquivo recebido via ssh
    nome_key_original = os.path.basename(vhost.get_ssl_certificate_key_file())
    os.rename(caminho_temp_novo_key, str(Path(pasta_destino_temp, nome_key_original)))
    caminho_temp_novo_key = str(Path(pasta_destino_temp, nome_key_original))
    # Verifica se os arquivos baixados .crt e .key correspondem
    compativeis = utils.comparar_crt_key(caminho_temp_novo_crt, caminho_temp_novo_key)
    if compativeis:
        utils.set_log_info("Certificados compativeis")
        # Cria backup local dos certificados vencidos
        criar_backup(path_completo_crt, path_completo_key)
        # Move os novos certificados da pasta temporaria para a pasta de certificados do apache
        utils.mover_arquivo(caminho_temp_novo_crt, path_crt)
        utils.mover_arquivo(caminho_temp_novo_key, path_key)


def atualizar_certificado(commonName: str, pathNewCert: str):
    utils.set_log_info("Executando script atualizacao.py")

    try:

        certificado_anterior = None
        certificado_atual = None
        envio_atualizacao = []
        itens_atualizados = []
        # Cria pasta temporaria para o download dos novos certificados
        pasta_destino_temp = utils.criar_pasta("temp_" + datetime.now().strftime("%d-%m-%Y"), utils.cwd)
        utils.set_log_info("Criada pasta temporaria em: " + str(pasta_destino_temp.absolute()))
        # Extrai arquivo com os certificados em uma pasta temporaria
        list_arquivos = utils.extrair_arquivos(pathNewCert, pasta_destino_temp)
        # Le os arquivos por extensao
        path_novo_arquivo_pem = ""
        for arquivo in list_arquivos:
            # Caso o zip contenha a cadeia de certificados em um arquivo separado
            if Path(arquivo).suffix == '.pem':
                path_novo_arquivo_pem = Path(arquivo)
            elif Path(arquivo).suffix == '.crt':
                path_novo_arquivo_crt = Path(arquivo)
            elif Path(arquivo).suffix == '.key':
                # Obtem o caminho para o novo arquivo .key
                path_novo_arquivo_key = Path(arquivo)

        # Verifica se existe nginx instalado
        if os.path.exists('/etc/nginx'):
            # ler todos os certificados configurados no host
            vhosts = nginx.obter_informacoes_vhosts_nginx()
            for vhost in vhosts:
                if vhost.get_info_config().get_status() != 'Erro':
                    cert = vhost.get_certificado()
                    # Se o commonName estiver em algum arquivo de configuracao
                    if cert['nomeCompleto'] == commonName:
                        # Comparar as chaves publicas dos certificados e verificar se os certificados sao os mesmos
                        certificados_iguais = utils.comparar_certificado(path_novo_arquivo_crt,
                                                                         vhost.get_ssl_certificate_file())
                        if certificados_iguais:
                            utils.set_log_info("Certificados ja estão configurados no servidor Nginx")
                        else:
                            path_completo_crt = vhost.get_ssl_certificate_file()
                            certificado_atual = utils.ler_certificado_crt(vhost.get_ssl_certificate_file())
                            certificado_anterior = utils.ler_certificado_crt(path_completo_crt)
                            itens_atualizados.append(ItemAtualizacaoDTO(certificado_anterior, certificado_atual))
                            # Funcao para atualizar o certificado
                            atualizar_certificado_nginx(vhost, pasta_destino_temp, path_novo_arquivo_pem,
                                                        path_novo_arquivo_crt, path_novo_arquivo_key)
                            # Verifica se a configuração possui erros
                            info_config = nginx.verificar_configuracao_nginx()
                            if info_config.get_status() == 'Erro':
                                utils.set_log_info("Nginx com erro de configuração")
                                # Voltar certificados antigos
                            else:
                                nginx.reload_nginx()
                                utils.set_log_info("Certificados atualizados com Sucesso")

        # Verifica se existe apache instalado
        if os.path.exists('/etc/apache2'):
            # ler todos os certificados configurados no host
            vhosts = apache.obter_informacoes_vhosts_apache()
            for vhost in vhosts:
                if vhost.get_info_config().get_status() != 'Erro':
                    cert = vhost.get_certificado()
                    if cert['nomeCompleto'] == commonName:
                        # Comparar as chaves publicas dos certificados e verificar se os certificados sao os mesmos
                        certificados_iguais = utils.comparar_certificado(path_novo_arquivo_crt,
                                                                         vhost.get_ssl_certificate_file())
                        if certificados_iguais:
                            utils.set_log_info("Certificados ja estão configurados no servidor Apache")
                        else:
                            path_completo_crt = vhost.get_ssl_certificate_file()
                            certificado_atual = utils.ler_certificado_crt(vhost.get_ssl_certificate_file())
                            certificado_anterior = utils.ler_certificado_crt(path_completo_crt)
                            itens_atualizados.append(ItemAtualizacaoDTO(certificado_anterior, certificado_atual))
                            # Passar as cadeias
                            atualizar_certificado_apache(vhost, pasta_destino_temp, path_novo_arquivo_crt,
                                                         path_novo_arquivo_key)
                            # Verifica se a configuração possui erros
                            info_config = apache.verificar_configuracao_apache()
                            if info_config.get_status() == 'Erro':
                                utils.set_log_info("Apache com erro de configuração")
                                # Voltar certificados antigos
                            else:
                                apache.reload_apache()
                                utils.set_log_info("Certificados atualizados com Sucesso")

        # Cria um envio
        file = open(utils.obter_log())
        log = file.read()
        file.close()

        envio_atualizacao.append(AtualizacaoDTO(ambiente.obter_host_name(), utils.obter_token_local(),
                                                ambiente.get_ip(), datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                datetime.now().strftime("%d/%m/%Y %H:%M:%S"), log,
                                                itens_atualizados).__dict__)

        # Remove a pasta temporaria de download
        shutil.rmtree(pasta_destino_temp)

        # Converte para JSON
        parsed_json = utils.converter_json(envio_atualizacao)
        return parsed_json

    except Exception as err:
        utils.set_log_error("Exceção Capturada")
        utils.set_log_error(err)
