import xml.dom.minidom
from collections import defaultdict
from pathlib import Path

def main():
    curriculos_dir = Path("curriculos")
    especialidades = defaultdict(list)

    for curriculo_path in curriculos_dir.glob("*.xml"):
        curriculo = xml.dom.minidom.parse(str(curriculo_path))
        dados_gerais = curriculo.getElementsByTagName("DADOS-GERAIS")
        nome_completo = dados_gerais[0].getAttribute("NOME-COMPLETO")
        areas_de_atuacao = curriculo.getElementsByTagName("AREA-DE-ATUACAO")
        for area in areas_de_atuacao:
            especialidade = area.getAttribute("NOME-DA-ESPECIALIDADE")
            if especialidade == "":
                especialidade = area.getAttribute("NOME-DA-SUB-AREA-DO-CONHECIMENTO")
                if especialidade == "":
                    especialidade = area.getAttribute("NOME-DA-AREA-DO-CONHECIMENTO")
                pass
            especialidades[nome_completo].append(especialidade)
    
    print(especialidades)



if __name__ == "__main__":
    main()