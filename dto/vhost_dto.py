class VhostDTO:

    def __init__(self, info_config, port=None, server_admin=None, server_name=None, server_alias=None,
                 ssl_certificate_file=None, ssl_certificate_key_file=None, ssl_certificate_chain_file=None,
                 path_file=None, certificado=None):
        self.infoConfig = info_config
        if port is not None:
            self.port = port
        if server_admin is not None:
            self.serverAdmin = server_admin
        if server_name is not None:
            self.serverName = server_name
        if server_alias is not None:
            self.serverAlias = server_alias
        if ssl_certificate_file is not None:
            self.sslcertificateFile = ssl_certificate_file
        if ssl_certificate_key_file is not None:
            self.sslcertificateKeyFile = ssl_certificate_key_file
        if ssl_certificate_chain_file is not None:
            self.sslcertificateChainFile = ssl_certificate_chain_file
        if path_file is not None:
            self.pathFile = path_file
        if certificado is not None:
            self.certificado = certificado

    def get_info_config(self):
        return self.infoConfig

    def get_certificado(self):
        return self.certificado

    def get_ssl_certificate_file(self):
        return self.sslcertificateFile

    def get_ssl_certificate_key_file(self):
        return self.sslcertificateKeyFile

    def get_path_file(self):
        return self.pathFile
