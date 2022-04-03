class ServidorDTO:
    def __init__(self, nome, versao, info_config, certificados=None):
        self.nome = nome
        self.versao = versao
        self.infoConfig = info_config
        self.certificados = certificados
