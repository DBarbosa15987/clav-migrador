import json
import html
import os
from path_utils import DUMP_DIR, PROJECT_ROOT,FILES_DIR

class Report:

    def __init__(self):
        self.declaracoes = {} # {"100":["100.ttl"], "200":["100.ttl","200.ttl"]}
        self.missingRels = {
            "relsSimetricas": [],
            "relsInverseOf": []
        }
        self.globalErrors = {
            "grave":{
                "declsRepetidas": {}, # {"200":["100.ttl","200.ttl"]}
                "relsInvalidas": {}, # {"200":["100.10.001","eCruzadoCom"]} -> "200" é mencionado por "100.10.001"
                "outro": {} # {"200": ["mensagem de erro"]}
            },
            "normal": {}, # {"200": ["mensagem de erro"]}
            "erroInv": {}, # {"rel_x_inv_y": [erroInv:ErroInv]}
            "erroInvByCod": {} # {"200": [erroInv:ErroInv]}
        }
        self.warnings = {}


    def addErro(self,cod,msg,grave=False):
        """
        Adiciona a `rep` um erro genérico, pode
        ou não ser marcado como "grave".
        """
        if grave:
            if cod in self.globalErrors["grave"]["outro"]:
                self.globalErrors["grave"]["outro"][cod].append(msg)
            else:
                self.globalErrors["grave"]["outro"][cod] = [msg]
        else:
            if cod in self.globalErrors["normal"]:
                self.globalErrors["normal"][cod].append(msg)
            else:
                self.globalErrors["normal"][cod] = [msg]


    def addMissingRels(self,proc,rel,cod,tipo):
        """Regista e guarda em `rep.missingRels` uma relação
        (`proc` `rel` `cod`) que está em falta, isto é, que
        não está declarada explicitamente.
        Uma "missingRel" pode ser de `tipo` **relsSimetricas**
        ou **relsInverseOf**.
        """
        self.missingRels[tipo].append((proc,rel,cod))


    def fixMissingRels(self,allClasses):
        """
        Função que infere e adiciona em `allClasses` as relações
        simétricas e inversas que estão declaradas implicitamente,
        tornando-as explícitas.
        """
        for r in self.missingRels["relsSimetricas"]:
            classe = allClasses.get(r[0])
            proRel = classe.get("proRel")
            proRelCod = classe.get("processosRelacionados")
            if proRel and proRelCod:
                classe["proRel"].append(r[1])
                classe["processosRelacionados"].append(r[2])
            else:
                classe["proRel"] = [r[1]]
                classe["processosRelacionados"] = [r[2]]
            self.addWarning("I",r)

        for r in self.missingRels["relsInverseOf"]:
            classe = allClasses.get(r[0])
            proRel = classe.get("proRel")
            proRelCod = classe.get("processosRelacionados")
            if proRel and proRelCod:
                classe["proRel"].append(r[1])
                classe["processosRelacionados"].append(r[2])
            else:
                classe["proRel"] = [r[1]]
                classe["processosRelacionados"] = [r[2]]
            self.addWarning("I",r)


    def addDecl(self,cod,fileName):
        # "cod" aparece declarado repetidamente no(s) ficheiro(s) set(declaracoes[cod])
        if cod in self.declaracoes:
            self.declaracoes[cod].append(fileName+".json")
        else:
            self.declaracoes[cod] = [fileName+".json"]


    def addRelInvalida(self,proRel,rel,cod,tipoProcRef=None):
        """
        Adiciona a `rep` uma relação inválida, ou seja, o processo
        `proRel` relaciona-se com um processo `cod` que não existe.

        O `tipoProcRef` indica o tipo de relação em questão, pode ter
        os valores de `None` (referente aos "processosRelacionados" de
        cada um processo), PCA ou DF.
        """
        # O dicionário representa: `cod` (inválido) é mencionado por relacoes[cod]
        relacoes = self.globalErrors["grave"]["relsInvalidas"]
        if proRel in relacoes:
            relacoes[proRel].append((cod,rel,tipoProcRef))
        else:
            relacoes[proRel] = [(cod,rel,tipoProcRef)]


    def checkStruct(self):
        # Verifica a existência de erros "graves" no código.
        ok = True
        repetidas = [(k,v) for k,v in self.declaracoes.items() if len(v)>1]
        if repetidas:
            self.globalErrors["grave"]["declsRepetidas"] = repetidas
            ok = False

        if len(self.globalErrors["grave"]["relsInvalidas"])>0:
            ok = False

        if len(self.globalErrors["grave"]["outro"])>0:
            ok = False

        return ok


    def addFalhaInv(self,inv,cod,info="",extra=""):
        """
        Regista em `rep` a falha de um invariante `inv`
        no processo `cod`. O info e extra server para a
        criação de mensagens de erro mais específicas.

        O `info` não é necessariamente uma `str`, também
        pode ser um `dict`, uma `list` ou um `tuple`,
        varia de acordo com erro.
        """
        if inv in self.globalErrors["erroInv"]:
            self.globalErrors["erroInv"][inv].append(ErroInv(inv,cod,info,extra))
        else:
            self.globalErrors["erroInv"][inv] = [ErroInv(inv,cod,info,extra)]


    def addWarning(self,tipo,info):

        match tipo:
            case "I":
                if "inferencias" in self.warnings:
                    self.warnings["inferencias"].append(f"{info[0]} :{info[1]} {info[2]}")
                else:
                    self.warnings["inferencias"] = [f"{info[0]} :{info[1]} {info[2]}"]
            case "H":
                if "harmonizacao" in self.warnings:
                    self.warnings["harmonizacao"].append(info)
                else:
                    self.warnings["harmonizacao"] = [info]
            case "R":
                if "relHarmonizacao" in self.warnings:
                    self.warnings["relHarmonizacao"].append(info)
                else:
                    self.warnings["relHarmonizacao"] = [info]

            case _:
                if "normal" in self.warnings:
                    self.warnings["normal"].append(info)
                else:
                    self.warnings["normal"] = [info]


    def errorsByCod(self):
        """
        Função que agrupa os erros por código,
        para ser mostrado no HTML.
        """

        errosInv = {}
        with open(os.path.join(FILES_DIR, "classesN1.json")) as f:
            classesN1 = json.load(f)
        for cod in classesN1:
            errosInv[cod] = []

        for errors in self.globalErrors["erroInv"].values():
            for err in errors:
                classeN1 = err.cod[:3]
                errosInv[classeN1].append(err)

        self.globalErrors["erroInvByCod"] = errosInv


    def dumpReport(self,dumpFileName="dump.json"):
        report = {}
        report["globalErrors"] = self.globalErrors
        report["warnings"] = self.warnings

        with open(os.path.join(DUMP_DIR, dumpFileName),'w') as f:
            json.dump(report,f,ensure_ascii=False,cls=CustomEncoder, indent=4)

    def generate_error_table(self):
        """
        Função que gera a tabela HTML que faz o display dos
        erros ocorridos durante a migração.

        Os erros são agrupados por tipo.
        """
        self.errorsByCod()
        with open(os.path.join(PROJECT_ROOT, "invariantes.json")) as f:
            invs = json.load(f)

        html_content = """
        <style>
            .error-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif; }
            .error-table th, .error-table td { border: 1px solid #ccc; padding: 10px; text-align: left; }
            .error-table th { background-color: #f2f2f2; font-weight: bold; }
            .error-section { background-color: #e0e0e0; font-size: 1.1em; font-weight: bold; padding: 10px; margin-top: 20px; }
            .msg { color: #444; font-style: italic; }
        </style>
        <div>
        """

        html_content += f'<div class="error-section">🟥 Erros Graves</div>\n'

        # Decls Repetidas (Grave)
        if self.globalErrors["grave"]["declsRepetidas"]:
            html_content += '<div class="error-section">Declarações Repetidas</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Ficheiros</th></tr>'
            for cod, files in self.globalErrors["grave"]["declsRepetidas"].items():
                html_content += f"<tr><td>{cod}</td><td>{', '.join(files)}</td></tr>"
            html_content += '</table>'

        # Rels Invalidas (Grave)
        if self.globalErrors["grave"]["relsInvalidas"]:
            html_content += '<div class="error-section">Relações Inválidas</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Relações</th></tr>'
            for cod, rels in self.globalErrors["grave"]["relsInvalidas"].items():
                html_content += f"<tr><td>{cod}</td><td><ul style='list-style-type: disc; padding-left: 1.25rem; margin: 0;'>"
                for rel in rels:
                    html_content += f"<li style='display: list-item;'>{cod} {rel[1]} {rel[0]}</li>"
                html_content += "</ul></td></tr>"
            html_content += '</table>'

        # Outros (Grave)
        if self.globalErrors["grave"]["outro"]:
            html_content += '<div class="error-section">Outros Erros Graves</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for cod, msgs in self.globalErrors["grave"]["outro"].items():
                for msg in msgs:
                    html_content += f"<tr><td>{cod}</td><td class='msg'>{html.escape(msg)}</td></tr>"
            html_content += '</table>'

        # Normal
        if self.globalErrors["normal"]:
            html_content += f'<div class="error-section">🟨 Erros Genéricos</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for cod, msgs in self.globalErrors["normal"].items():
                for msg in msgs:
                    html_content += f"<tr><td>{cod}</td><td class='msg'>{html.escape(msg)}</td></tr>"
            html_content += '</table>'

        # Invariantes
        if self.globalErrors["erroInv"]:
            html_content += f'<div class="error-section">🟦 Erros de Invariantes</div>\n'
            for inv, erros in self.globalErrors["erroInv"].items():
                invariante = invs.get(inv, {"desc": "Sem descrição", "clarificacao": ""})
                errTitle = f"{inv} ({len(erros)}): {invariante['desc']}"
                if invariante["clarificacao"]:
                    errTitle += f" ({invariante['clarificacao']})"
                html_content += f'<div class="error-section">{errTitle}</div>\n'
                html_content += """
                <table class="error-table">
                    <tr><th>Código</th><th>Mensagem de Erro</th></tr>
                """
                for err in erros:
                    cod = err.cod
                    msg = html.escape(err.msg)
                    html_content += f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
                html_content += "</table>\n"

        html_content += "</div>"
        return html_content


    def generate_entity_table_dict(self):
        """
        Gera um dicionário indexado por entidade da AP
        em que o seu valor é a tabela HTML correspondente.
        """
        self.errorsByCod()
        with open(os.path.join(FILES_DIR, "classesN1.json")) as f:
            classesN1 = json.load(f)

        entity_tables = {}

        def addRow(entity_dict, ent, content):
            if ent not in entity_dict:
                entity_dict[ent] = ''
            entity_dict[ent] += content

        def getEnt(cod):
            ent = cod
            try:
                ent = cod[:3]
            except Exception:
                pass
            return ent

        # Declarações Repetidas
        for cod, files in self.globalErrors["grave"]["declsRepetidas"].items():
            html_part = f'<div class="error-section">Declarações Repetidas</div>\n'
            html_part += '<table class="error-table"><tr><th>Código</th><th>Ficheiros</th></tr>'
            html_part += f"<tr><td>{cod}</td><td>{', '.join(files)}</td></tr></table>"
            ent = getEnt(cod)
            addRow(entity_tables, ent, html_part)

        # Relações Inválidas
        for cod, rels in self.globalErrors["grave"]["relsInvalidas"].items():
            html_part = f'<div class="error-section">Relações Inválidas</div>\n'
            html_part += '<table class="error-table"><tr><th>Código</th><th>Relações</th></tr>'
            html_part += f"<tr><td>{cod}</td><td><ul style='list-style-type: disc; padding-left: 1.25rem; margin: 0;'>"
            for rel in rels:
                html_part += f"<li style='display: list-item;'>{cod} {rel[1]} {rel[0]}</li>"
            html_part += "</ul></td></tr></table>"
            ent = getEnt(cod)
            addRow(entity_tables, ent, html_part)

        # Outros Erros Graves
        for cod, msgs in self.globalErrors["grave"]["outro"].items():
            html_part = f'<div class="error-section">Outros Erros Graves</div>\n'
            html_part += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for msg in msgs:
                html_part += f"<tr><td>{cod}</td><td class='msg'>{html.escape(msg)}</td></tr>"
            html_part += "</table>"
            ent = getEnt(cod)
            addRow(entity_tables, ent, html_part)

        # Erros Normais
        for cod, msgs in self.globalErrors["normal"].items():
            html_part = f'<div class="error-section">Erros Genéricos</div>\n'
            html_part += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for msg in msgs:
                html_part += f"<tr><td>{cod}</td><td class='msg'>{html.escape(msg)}</td></tr>"
            html_part += "</table>"
            ent = getEnt(cod)
            addRow(entity_tables, ent, html_part)

        # Erros de Invariantes por entidade
        for cod, erros in self.globalErrors["erroInvByCod"].items():
            invariante = classesN1.get(cod, {"titulo": "Sem descrição", "clarificacao": ""})
            errTitle = f"{cod} ({len(erros)}): {invariante['titulo']}"
            html_part = f'<div class="error-section">Erros de Invariantes</div>\n'
            html_part += f'<div class="error-section">{errTitle}</div>\n'
            html_part += '<table class="error-table"><tr><th>Código</th><th>Mensagem de Erro</th></tr>'
            for err in erros:
                html_part += f"<tr><td>{err.cod}</td><td class='msg'>{html.escape(err.msg)}</td></tr>"
            html_part += "</table>"
            addRow(entity_tables, cod, html_part)

        return entity_tables


class ErroInv:

    def __init__(self,inv,cod,info,extra):
        self.inv = inv
        self.cod = cod
        self.info = info
        self.extra = extra
        self.fixed = False
        self.fixedMsg = ""
        self.msg = self.errorMsg()

    def fix(self,fixedMsg):
        self.fixed = True
        self.fixedMsg = fixedMsg

    def errorMsg(self):
        msg = ""
        match self.inv:
            case "rel_4_inv_0": # OK
                msg = f"O processo {self.cod} não desdobramento ao nível 4, mas não contém justificação associada ao PCA."
            case "rel_4_inv_11": # OK
                msg = f"No processo {self.cod} foram encontradas relações de \"eSinteseDe\" e \"eSintetizadoPor\" em simultâneo:\n"
                for rel in self.info:
                    msg += f"\t{self.cod} {rel[1]} {rel[0]}\n"
            case "rel_4_inv_12": # OK
                msg = f"A legislação {self.info} é referenciada na justificação do {self.extra["tipo"]} do processo {self.cod}, mas não se encontra devidamente declarada."
            case "rel_4_inv_13": # OK
                msg = f"A legislação {self.info} é referenciada na justificação do {self.extra["tipo"]} do processo {self.cod}, mas não se encontra devidamente declarada (devia estar declarada na coluna \"Diplomas jurídico-administrativos REF\" do seu processo pai: {self.extra["pai"]})."
            case "rel_3_inv_6": # TODO: TEST
                temPca = self.info["temPca"]
                temDf = self.info["temDf"]
                x = ""
                if not temPca and not temDf:
                    x = "PCA nem DF"
                elif not temDf:
                    x = "DF"
                elif not temPca:
                    x = "PCA"
                msg = f"O processo {self.cod} não tem desdobramento ao nível 4 e não tem {x}."
            case "rel_3_inv_3": # OK
                msg = f"Os filhos ({self.info[0]} e {self.info[1]}) do processo {self.cod} tem DFs diferentes, mas não têm uma relação de síntese entre eles."
            case "rel_5_inv_1": # TODO: TEST extra
                msg = f"O processo {self.cod} é suplemento para outro, mas não contém um critério de utilidade administrativa na justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_5_inv_2": # TODO: TEST extra
                msg = f"O processo {self.cod} tem uma relação de \"suplementoPara\" com o processo {self.info}, mas este não é mencionado no critério de utilidade da justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_7_inv_2":  # TODO: TEST um dos extras
                msg = f"O processo {self.cod} é complementar de outro, no entanto a sua justificação não contém o critério de complementaridade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_6_inv_2": # OK parcial
                # FIXME: falta ver se isto não é redundante (rel_9_inv_3)
                if self.info:
                    msg = f"O processo {self.cod} é sintetizado por outro, mas o seu DF tem o valor de \"{self.info}\", em vez de \"Eliminação\""
                else:
                    msg = f"O processo {self.cod} é sintetizado por outro e o valor do seu DF devia ser \"Eliminação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_5_inv_3": # OK...
                msg = f"O processo {self.cod} contém relações de \"eSuplementoDe\" no processo {self.info}. No entanto estes não são mencionados na justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_9_inv_2": # OK
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\", mas tem o valor de DF de \"{self.info}\", em vez de \"Conservação\""
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_3_inv_1": # TODO: TEST
                # TODO: imprimir a lista melhor
                msg = f"O processo {self.cod} tem desdobramento, mas os seus filhos ({self.info["filhos"]}) têm valores de PCA e DF iguais ({self.info["valor"]})"
            case "rel_3_inv_5": # TODO: TEST
                temPca = self.info["temPca"]
                temDf = self.info["temDf"]
                x = ""
                if not temPca and not temDf:
                    x = "PCA nem DF"
                elif not temDf:
                    x = "DF"
                elif not temPca:
                    x = "PCA"
                msg = f"O processo {self.cod} tem desdobramento ao nível 4 e mesmo assim tem {x}."
            case "rel_3_inv_7": # TODO: TEST
                msg = f"O processo {self.cod} tem uma relação de \"complementar de\" com o processo {self.info["proc"]} e nenhum dos filhos ({self.info["filhos"]}) tem um valor de DF de \"Conservação\""
            case "rel_3_inv_4": # OK
                msg = f"O termo \"{self.info["termo"]}\" do processo {self.cod} não foi replicado para o seu filho {self.info["filho"]}"
            case "rel_6_inv_3": # TODO: TEST extra
                msg = f"No processo {self.cod} não consta uma justificação com critério de densidade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_6_inv_4": # TODO: TEST extra
                msg = f"O processo {self.info} está em falta na justificação do DF do processo {self.cod}, sob o critério de densidade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_9_inv_3": # OK parcial
                # FIXME: falta ver se isto não é redundante (rel_6_inv_2)
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSintetizadoPor\", mas tem o valor de DF de \"{self.info}\""
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSintetizadoPor\" e o valor do seu DF devia ser \"Eliminação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_7_inv_3": # OK
                msg = f"O processo {self.info} está em falta na justificação do DF do processo {self.cod}, sob o critério de complementaridade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_9_inv_1": # TODO: TEST
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eComplementarDe\", mas tem o valor de DF de {self.info}"
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eComplementarDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
            case "rel_4_inv_8": # OK
                relacoes = ""
                # Aqui sabe-se que terá sempre mais que 1 elemento
                for rel in self.info["rels"][:-1]:
                    relacoes += f"\"{self.cod} {rel[1]} {rel[0]}\", "
                ultimaRel = self.info["rels"][-1]
                relacoes += f"e \"{self.cod} {ultimaRel[1]} {ultimaRel[0]}\""
                msg = f"O processo {self.cod} tem mais do que uma relação com o processo {self.info["proc"]} ({relacoes})."
            case "rel_6_inv_1": # TODO: TEST
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\", mas tem o valor de DF de {self.info}, em vez de \"Conservação\""
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_4_inv_1_0": # OK
                msg = f"O processo {self.cod} não é transversal, no entanto foram encontrados participantes associados a ele."
            case "rel_4_inv_3": # OK
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_4": # OK
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_5": # OK, mas por testar
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_6": # OK, mas por testar
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_2": # OK
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_10": # TODO: TEST
                # TODO: indexar por termo??
                msg = f"O termo {self.info["t"]} foi encontrado repetido nos seguintes processos {self.info["cods"]}"
            case "rel_4_inv_7": # TODO: TEST
                msg = f"O processo {self.cod} relaciona-se com ele próprio, através da relação {self.info}"
            case "rel_8_inv_1": # TODO: TEST
                msg = f"No DF do processo {self.cod} foi encontrado uma justificação do tipo {self.info}"
            case "rel_4_inv_14": # TODO: TEST
                msg = f"O processo {self.cod} é transversal, mas não tem participantes"
            case "rel_3_inv_9": # OK
                msg = f"O processo {self.info} está em harmonização, no entanto o seu filho \"{self.cod}\" está ativo."
            case _:
                pass
        return msg

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__
