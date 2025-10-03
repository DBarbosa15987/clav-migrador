import json
import html
import os
from path_utils import DUMP_DIR
import logging
from log_utils import PROC
from enum import Enum
import html


class Report:

    def __init__(self):
        self.declaracoes = {} # {"100":["100_csv"], "200":["100_csv","200_csv"]}
        self.missingRels = {
            "relsSimetricas": [],
            "relsInverseOf": []
        }
        self.globalErrors = {
            "grave":{
                "declsRepetidas": {}, # {"200":["100_csv","200_csv"]}
                "relsInvalidas": {}, # {"200":["100.10.001","eCruzadoCom"]} -> "200" é mencionado por "100.10.001"
                "outro": {} # {"200": ["mensagem de erro"]}
            },
            "normal": {}, # {"200": ["mensagem de erro"]}
            "erroInv": {}, # {"rel_x_inv_y": [erroInv:ErroInv]}
            "erroInvByEnt": {}, # {"200": [erroInv:ErroInv]}
            "outro": {
                "leg": [],
                "tindice": [],
                "tipologia": [],
                "entidade": []
            }
        }
        self.warnings = {
            "inferencias": [],
            "harmonizacao": [],
            "relHarmonizacao": [],
            "normal": []
        }
        self.inativos = set()
        self.classesN1 = {}


    def addClasseN1(self,cod,titulo,desc):
        """
        Addiciona a rep.classesN1 a classe de nível 1
        juntamente com o seu título e descrição. Este
        método também adiciona as classes de nível 1
        como chaves do rep.erroInvByEnt.
        """
        self.globalErrors["erroInvByEnt"][cod] = {}
        self.classesN1[cod] = {
            "titulo": titulo,
            "descricao": desc
        }


    def addInativo(self,cod):
        self.inativos.add(cod)


    def addErro(self,cod,msg,grave=False):
        """
        Adiciona ao `rep` um erro genérico, pode
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


    def addErroNoCod(self,msg,categ):
        """
        Adiciona ao `rep` um erro do tipo "outro", que
        representa um erro que ocorreu na extração dos
        dados que não são identificados por um código
        como o das classes.
        """
        if categ in self.globalErrors["outro"]:
            self.globalErrors["outro"][categ].append(msg)


    def addMissingRels(self,proc,rel,cod,tipo):
        """
        Regista e guarda em `Report.missingRels` uma relação
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

        logger = logging.getLogger(PROC)

        for r in self.missingRels["relsSimetricas"]:
            classe = allClasses.get(r[0])
            if classe:
                proRel = classe.get("proRel")
                proRelCod = classe.get("processosRelacionados")
                if proRel and proRelCod:
                    classe["proRel"].append(r[1])
                    classe["processosRelacionados"].append(r[2])
                else:
                    classe["proRel"] = [r[1]]
                    classe["processosRelacionados"] = [r[2]]
                self.addWarning("I",{"rel":r})

        logger.info(f"Foram efetuadas {len(self.missingRels["relsSimetricas"])} inferências de relações simétricas")

        for r in self.missingRels["relsInverseOf"]:
            classe = allClasses.get(r[0])
            if classe:
                proRel = classe.get("proRel")
                proRelCod = classe.get("processosRelacionados")
                if proRel and proRelCod:
                    classe["proRel"].append(r[1])
                    classe["processosRelacionados"].append(r[2])
                else:
                    classe["proRel"] = [r[1]]
                    classe["processosRelacionados"] = [r[2]]
                self.addWarning("I",{"rel":r})

        logger.info(f"Foram efetuadas {len(self.missingRels["relsInverseOf"])} inferências de relações inversas")


    def addDecl(self,cod,sheet):
        # "cod" aparece declarado na(s) folha(s) self.declaracoes[cod]
        if cod in self.declaracoes:
            self.declaracoes[cod].append(sheet)
        else:
            self.declaracoes[cod] = [sheet]


    def addRelInvalida(self,proRel,rel,cod,tipoProcRef=None):
        """
        Adiciona a `rep` uma relação inválida, ou seja, o processo
        `proRel` relaciona-se com um processo `cod`, que não existe.

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
        logger = logging.getLogger(PROC)
        repetidas = {k:set(v) for k,v in self.declaracoes.items() if len(v)>1}
        if repetidas:
            self.globalErrors["grave"]["declsRepetidas"] = repetidas
            ok = False

        if len(self.globalErrors["grave"]["relsInvalidas"])>0:
            ok = False


        if len(self.globalErrors["grave"]["outro"])>0:
            ok = False

        if not ok:
            logger.warning("Foram encontrados erros graves nos dados, a ontologia final não será criada")

        return ok


    def addFalhaInv(self,inv,cod,info={},extra=""):
        """
        Regista em `rep` a falha de um invariante `inv`
        no processo `cod`. As falhas de invariante são
        indexadas por invariante e por código em
        rep.globalErrors["erroInv"] e
        rep.globalErrors["erroInvByEnt"], respetivamente.

        O `info` e `extra` serve para a criação de mensagens
        de erro. O `info` é um `dict`, no entanto não contém
        entradas iguais, depende sempre do invariante.
        """

        err = ErroInv(inv,cod,info,extra)
        # Aqui consulta-se sempre o self.declaracoes caso o
        # código esteja com um formato inválido para saber
        # onde a classe foi declarada. Neste caso só olhamos
        # para a primeira declaração.
        if sheets := self.declaracoes.get(cod):
            ent = sheets[0].replace("_csv","")
            if inv in self.globalErrors["erroInvByEnt"][ent]:
                self.globalErrors["erroInvByEnt"][ent][inv].append(err)
            else:
                self.globalErrors["erroInvByEnt"][ent][inv] = [err]


        if inv in self.globalErrors["erroInv"]:
            self.globalErrors["erroInv"][inv].append(err)
        else:
            self.globalErrors["erroInv"][inv] = [err]


    def addWarning(self,tipo="",info={}):

        match tipo:
            case "I":
                self.warnings["inferencias"].append(f"A relação \"<b>{info["rel"][0]}</b> <b><i>{info["rel"][1]}</b></i> <b>{info["rel"][2]}</b>\" foi inferida automaticamente")
            case "H":
                self.warnings["harmonizacao"].append(f"O processo <b>{info["proc"]}</b> está em harmonização")
            case "R":
                self.warnings["relHarmonizacao"].append(f"Foi encontrada a relação \"<b>{info["rel"][0]}</b> <b><i>{info["rel"][1]}</b></i> <b>{info["rel"][2]}</b>\", na qual <b>{info["rel"][2]}</b> está em harmonização")
            case _:
                self.warnings["normal"].append(info["msg"])


    def dumpReport(self,dumpFileName="dump.json"):
        report = {}
        report["globalErrors"] = self.globalErrors
        report["warnings"] = self.warnings
        logger = logging.getLogger(PROC)

        dumpPath = os.path.join(DUMP_DIR, dumpFileName)
        try:
            logger.info(f"Criação de um dump do relatório de erros: {dumpPath}")
            with open(dumpPath,'w') as f:
                json.dump(report,f,ensure_ascii=False,cls=CustomEncoder, indent=4)
        except Exception as e:
            logger.error(f"Criação do dump do relatório de erros falhou")
            logger.exception(f"[{e.__class__.__name__}]: {e}")


class FixStatus(Enum):
    FAILED = -1
    UNFIXED = 0
    FIXED = 1


class ErroInv:

    def __init__(self,inv,cod,info,extra):
        self.inv = inv
        self.cod = html.escape(cod)
        self.info = self.escapeAllHtml(info)
        self.extra = html.escape(extra)
        self.fixStatus = FixStatus.UNFIXED
        self.fixMsg = ""
        self.msg = self.errorMsg()


    def escapeAllHtml(self,data):
        if isinstance(data, str):
            return html.escape(data)
        elif isinstance(data, list):
            return [self.escapeAllHtml(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.escapeAllHtml(value) for key, value in data.items()}
        elif isinstance(data, tuple):
            return tuple(self.escapeAllHtml(item) for item in data)
        else:
            return data


    def fix(self, fixMsg):
        self.fixStatus = FixStatus.FIXED
        self.fixMsg = fixMsg


    def fail(self,fixMsg):
        self.fixStatus = FixStatus.FAILED
        self.fixMsg = fixMsg


    def errorMsg(self):
        """
        Função que gera a mensagem de erro de acordo com
        o invariante. Estas mensagens serão inseridas numa
        tabela html e por isso contêm tags html.
        """

        def getDfValue(abrev):

            dfAbrevDic = {
                "C": "Conservação",
                "CP": "Conservação Parcial",
                "E": "Eliminação"
            }

            return dfAbrevDic.get(abrev,abrev)

        msg = ""
        match self.inv:
            case "rel_2_inv_1":
                msg = f"O processo <b>{self.cod}</b> não tem desdobramento ao nível 4, mas não contém justificação associada ao PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_2_inv_11":
                msg = f"No processo <b>{self.cod}</b> foram encontradas relações de <i><b>eSinteseDe</b></i> e <i><b>eSintetizadoPor</b></i> em simultâneo: "
                msg += ", ".join([f"\"<b>{self.cod}</b> <i><b>{r[1]}</i></b> <b>{r[0]}</b>\"" for r in self.info["sinteses"]])
                msg += "."
            case "rel_2_inv_12":
                msg = f"A legislação <b>{self.info["leg"]}</b> é referenciada na justificação do <b>{self.info["tipo"]}</b> do processo <b>{self.cod}</b>, mas não se encontra devidamente declarada."
            case "rel_2_inv_13":
                msg = f"A legislação <b>{self.info["leg"]}</b> é referenciada na justificação do <b>{self.info["tipo"]}</b> do processo <b>{self.cod}</b>, mas não se encontra devidamente declarada (devia estar declarada na coluna \"Diplomas jurídico-administrativos REF\" do seu processo pai: {self.info["pai"]})."
            case "rel_1_inv_5":
                temPca = self.info["temPca"]
                temDf = self.info["temDf"]
                x = ""
                if not temPca and not temDf:
                    x = "PCA nem DF"
                elif not temDf:
                    x = "DF"
                elif not temPca:
                    x = "PCA"
                msg = f"O processo <b>{self.cod}</b> não tem desdobramento ao nível 4 e não tem {x}."
            case "rel_1_inv_2":
                msg = f"Os filhos (<b>{self.info["codF1"]}</b> e <b>{self.info["codF2"]}</b>) do processo <b>{self.cod}</b> tem DFs diferentes, mas não têm uma relação de síntese entre eles."
            case "rel_3_inv_1":
                msg = f"O processo <b>{self.cod}</b> é suplemento para outro, mas não contém um <b>critério de utilidade administrativa</b> na justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_3_inv_2":
                msg = f"O processo <b>{self.cod}</b> tem uma relação de <i><b>eSuplementoPara</i></b> com o processo <b>{self.info["proc"]}</b>, mas este não é mencionado no <b>critério de utilidade</b> da justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_5_inv_1":
                msg = f"O processo <b>{self.cod}</b> é complementar de outro, no entanto a sua justificação não contém o <b>critério de complementaridade informacional</b>"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_4_inv_1":
                if self.info["valor"]:
                    msg = f"O processo <b>{self.cod}</b> é sintetizado por outro, mas o seu DF tem o valor de \"{getDfValue(self.info["valor"])}\", em vez de \"Eliminação\""
                else:
                    msg = f"O processo <b>{self.cod}</b> é sintetizado por outro e o valor do seu DF devia ser \"Eliminação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_3_inv_3":
                msg = f"O processo <b>{self.cod}</b> contém relações de <i><b>eSuplementoDe</i></b> no processo <b>{self.info["proc"]}</b>, no entanto estes não são mencionados na justificação do PCA"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_8_inv_2":
                if self.info["valor"]:
                    msg = f"O processo <b>{self.cod}</b> contém uma relação de <i><b>eSinteseDe</b></i>, mas tem o valor de DF de \"{getDfValue(self.info["valor"])}\", em vez de \"Conservação\""
                else:
                    msg = f"O processo <b>{self.cod}</b> contém uma relação de <i><b>eSinteseDe</b></i> e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_1_inv_1":
                msg = f"O processo <b>{self.cod}</b> tem desdobramento, mas os seus filhos (<b>{', '.join(self.info["filhos"])}</b>) têm valores de PCA e DF iguais."
            case "rel_1_inv_4":
                temPca = self.info["temPca"]
                temDf = self.info["temDf"]
                x = ""
                if temPca and temDf:
                    x = "PCA e DF"
                elif temDf:
                    x = "DF"
                elif temPca:
                    x = "PCA"
                msg = f"O processo <b>{self.cod}</b> tem desdobramento ao nível 4 e mesmo assim tem {x}."
            case "rel_1_inv_6":
                msg = f"O processo <b>{self.cod}</b> tem uma relação de <i><b>eComplementarDe</i></b> com o processo <b>{self.info["proc"]}</b> e nenhum dos filhos ({', '.join(self.info["filhos"])}) tem um valor de DF de \"Conservação\"."
            case "rel_1_inv_3":
                msg = f"O termo \"{self.info["termo"]}\" do processo <b>{self.cod}</b> não foi replicado para o seu filho <b>{self.info["filho"]}</b>."
            case "rel_4_inv_2":
                msg = f"No processo <b>{self.cod}</b> não consta uma justificação com <b>critério de densidade informacional</b>"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_4_inv_3":
                msg = f"O processo <b>{self.info["proc"]}</b> está em falta na justificação do DF do processo <b>{self.cod}</b>, sob o critério de densidade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_5_inv_2":
                msg = f"O processo <b>{self.info["proc"]}</b> está em falta na justificação do DF do processo <b>{self.cod}</b>, sob o critério de complementaridade informacional"
                if self.extra:
                    msg += f" ({self.extra})"
                msg += "."
            case "rel_8_inv_1":
                if self.info["valor"]:
                    msg = f"O processo <b>{self.cod}</b> contém uma relação de <i><b>eComplementarDe</i></b>, mas tem o valor de DF de \"{getDfValue(self.info["valor"])}\"."
                else:
                    msg = f"O processo <b>{self.cod}</b> contém uma relação de <i><b>eComplementarDe</i></b> e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF."
            case "rel_2_inv_9":
                relacoes = ""
                # Aqui sabe-se que terá sempre mais que 1 elemento
                for rel in self.info["rels"][:-1]:
                    relacoes += f"\"<b>{self.cod}</b> <i><b>{rel[1]}</i></b> <b>{rel[0]}</b>\", "
                ultimaRel = self.info["rels"][-1]
                relacoes += f"\"<b>{self.cod}</b> <i><b>{ultimaRel[1]}</i></b> <b>{ultimaRel[0]}</b>\""
                msg = f"O processo <b>{self.cod}</b> tem mais do que uma relação com o processo <b>{self.info["proc"]}</b> ({relacoes})."
            case "rel_2_inv_2":
                msg = f"O processo <b>{self.cod}</b> não é transversal, no entanto foram encontrados participantes associados a ele."
            case "rel_2_inv_4":
                msg = f"Foram encontradas as relações \"<b>{self.cod}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.info["c"]}</b>\" e \"<b>{self.info["c"]}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.cod}</b>\". Estas duas relações não podem existir em simultâneo."
            case "rel_2_inv_5":
                msg = f"Foram encontradas as relações \"<b>{self.cod}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.info["c"]}</b>\" e \"<b>{self.info["c"]}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.cod}</b>\". Estas duas relações não podem existir em simultâneo."
            case "rel_2_inv_6":
                msg = f"Foram encontradas as relações \"<b>{self.cod}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.info["c"]}</b>\" e \"<b>{self.info["c"]}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.cod}</b>\". Estas duas relações não podem existir em simultâneo."
            case "rel_2_inv_7":
                msg = f"Foram encontradas as relações \"<b>{self.cod}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.info["c"]}</b>\" e \"<b>{self.info["c"]}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.cod}</b>\". Estas duas relações não podem existir em simultâneo."
            case "rel_2_inv_3":
                msg = f"Foram encontradas as relações \"<b>{self.cod}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.info["c"]}</b>\" e \"<b>{self.info["c"]}</b> <i><b>{self.info["rel"]}</b></i> <b>{self.cod}</b>\". Estas duas relações não podem existir em simultâneo."
            case "rel_2_inv_10":
                msg = f"O termo \"{self.info["t"]}\" foi encontrado repetido nos seguintes processos: <b>{", ".join(self.info["cods"])}</b>."
            case "rel_2_inv_8":
                msg = f"O processo <b>{self.cod}</b> relaciona-se com ele próprio, através da relação <i><b>{self.info["rel"]}</b></i>."
            case "rel_2_inv_14":
                msg = f"O processo <b>{self.cod}</b> é transversal, mas não tem participantes."
            case "rel_1_inv_7":
                msg = f"O processo <b>{self.info["pai"]}</b> está em harmonização, no entanto o seu filho <b>{self.cod}</b> está ativo."
            case "rel_8_inv_3":
                msg = f"O processo <b>{self.cod}</b> referencia o processo <b>{self.info["proc"]}</b> na justificação do \"<b>{self.info["tipo"]}</b>\", mas <b>{self.info["proc"]}</b> não está devidamente declarado."
            case "rel_8_inv_4":
                msg = f"O processo <b>{self.cod}</b> referencia o processo <b>{self.info["proc"]}</b>, mas <b>{self.info["proc"]}</b> não está declarado com a relação <i><b>eSuplementoPara</b></i>."
            case "rel_8_inv_5":
                msg = f"O processo <b>{self.cod}</b> referencia o processo <b>{self.info["proc"]}</b>, mas <b>{self.info["proc"]}</b> não está declarado com uma relação de síntese (<i><b>eSintetizadoPor</i></b>/<i><b>eSinteseDe</i></b>)."
            case "rel_8_inv_6":
                msg = f"O processo <b>{self.cod}</b> referencia o processo <b>{self.info["proc"]}</b>, mas <b>{self.info["proc"]}</b> não está declarado com a relação <i><b>eComplementarDe</b></i>."
            case "rel_7_inv_1":
                msg = f"Na justificação do PCA do processo <b>{self.cod}</b> foram encontrados mais do que um critério do tipo \"<b>{self.info["tipo"]}</b>\"."
            case "rel_6_inv_1":
                msg = f"Na justificação do DF do processo <b>{self.cod}</b> foram encontrados mais do que um critério do tipo \"<b>{self.info["tipo"]}</b>\"."
            case _:
                pass
        return msg


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        return obj.__dict__
