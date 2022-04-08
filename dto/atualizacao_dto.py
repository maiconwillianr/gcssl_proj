class AtualizacaoDTO:

    def __init__(self, host, token, ip, data_atualizacao, data_envio, log_param,
                 certificadoAnterior=None, certificadoAtual=None):
        self.host = host
        self.token = token
        self.ip = ip
        self.certificadoAnterior = certificadoAnterior
        self.certificadoAtual = certificadoAtual
        self.dataAtualizacao = data_atualizacao
        self.dataEnvio = data_envio
        self.log = log_param
