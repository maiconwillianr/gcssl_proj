class CertificadoDTO:

    def __init__(self, nome=None, emissor=None, path=None, md5=None,
                 data_criacao=None, data_validade=None, vencido=None):
        if nome is not None:
            self.nomeCompleto = nome
        if emissor is not None:
            self.emissor = emissor
        if path is not None:
            self.path = path
        if md5 is not None:
            self.md5 = md5
        if data_criacao is not None:
            self.dataEmissao = data_criacao
        if data_validade is not None:
            self.dataVencimento = data_validade
        if vencido is not None:
            self.vencido = vencido

    def get_md5(self):
        return self.md5
