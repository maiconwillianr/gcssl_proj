import json

import typer

import apache
import nginx
from ambiente import obter_informacoes_host_json
from atualizacao import atualizar_certificado

app = typer.Typer()


@app.command()
def status():
    typer.echo('OK')


@app.command()
def infohost():
    host_info = obter_informacoes_host_json()
    host_info = json.dumps(host_info, sort_keys=True, indent=4)
    typer.echo(host_info)


@app.command()
def listcertificates(server: str):
    certificados = []
    if server == 'apache':
        certificados = apache.listar_certificados()
    elif server == 'nginx':
        certificados = nginx.listar_certificados()
    else:
        typer.echo('Servidor nao reconhecido')

    if certificados:
        certificados = json.dumps(certificados, sort_keys=True, indent=4)
        typer.echo(certificados)
    else:
        typer.echo('Nenhum certificado encontrado')


@app.command()
def view(common_name: str):
    certificados = apache.listar_certificados()
    for cert in certificados:
        cert['nomeCompleto'] == common_name
        typer.echo(cert)


@app.command()
def update(common_name: str, path_new_cert: str):
    atualizacao_info = atualizar_certificado(common_name, path_new_cert)
    typer.echo(atualizacao_info)


if __name__ == "__main__":
    app()
