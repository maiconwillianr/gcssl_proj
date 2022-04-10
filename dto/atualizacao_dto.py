class AtualizacaoDTO:

    def __init__(self, host, token, ip, data_atualizacao, data_envio, log_param,
                 lista_itens_atualizados=None):
        self.host = host
        self.token = token
        self.ip = ip
        self.listaItensAtualizados = lista_itens_atualizados
        self.dataEnvio = data_envio
        self.dataAtualizacao = data_atualizacao
        self.log = log_param
