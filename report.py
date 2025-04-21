import json

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
            "erroInv": {} # {"rel_x_inv_y": [erroInv:ErroInv]}
        }
        self.warnings = {}


    def addErro(self,cod,msg,grave=False):
        # Adiciona um erro genérico, pode ou não ser marcado como "grave"
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
        # O "triplo" proc :rel cod está em falta
        self.missingRels[tipo].append((proc,rel,cod))


    def fixMissingRels(self,allClasses):

        # Estas "missingRels" referem-se às inferências que
        # seriam feitas, baseadas na definição da ontologias
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
        # "cod" é mencionado por relacoes[cod]
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
        # Aqui `info` pode ser uma string, uma lista ou um tuplo,
        # dependendo do invariante
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


    def printInv(self):

        for inv,info in self.globalErrors["erroInv"].items():
            # Em "erroInv" os values() são (cod,msg,extra)
            print(f"\n{inv} ({len(info)}):\n")
            pass


    def dumpReport(self,dumpFileName="dump.json"):
        report = {}
        report["globalErrors"] = self.globalErrors
        report["warnings"] = self.warnings

        with open(f"dump/{dumpFileName}",'w') as f:
            json.dump(report,f,ensure_ascii=False,cls=CustomEncoder, indent=4)

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
            case "rel_4_inv_0":
                msg = f"O processo {self.cod} não desdobramento ao nível 4, mas não contém justificação associada ao PCA"
            case "rel_4_inv_11":
                msg = f"No processo {self.cod} foram encontradas relações de \"eSinteseDe\" e \"eSintetizadoPor\" em simultâneo:\n"
                for rels in self.info:
                    msg += f"\t{self.cod} {self.info[1]} {self.info[0]}"
            case "rel_4_inv_12":
                msg = f"A legislação {self.info} é referenciada na justificação do {self.extra["tipo"]} do processo {self.cod}, mas não se encontra devidamente declarada"
            case "rel_4_inv_13":
                msg = f"A legislação {self.info} é referenciada na justificação do {self.extra["tipo"]} do processo {self.cod}, mas não se encontra devidamente declarada (devia estar declarada na coluna \"Diplomas jurídico-administrativos REF\" do seu processo pai: {self.extra["pai"]})"
            case "rel_3_inv_6":
                temPca = self.info["temPca"]
                temDf = self.info["temDf"]
                x = ""
                if not temPca and not temDf:
                    x = "PCA nem DF"
                elif not temDf:
                    x = "DF"
                elif not temPca:
                    x = "PCA"
                msg = f"O processo {self.cod} não tem desdobramento ao nível 4 e não tem {x}"
            case "rel_3_inv_3":
                msg = f"Os filhos ({self.info[0]} e {self.info[1]}) do processo {self.cod} tem DFs diferentes, mas não têm uma relação de síntese entre eles"
            case "rel_5_inv_1":
                msg = f"O processo {self.cod} é suplemento para outro, mas não contém um critério de utilidade administrativa na justificação do PCA ({self.extra})"
            case "rel_5_inv_2":
                msg = f"O processo {self.cod} tem uma relação de \"suplementoPara\" com o processo {self.info}, mas este não é mencionado no critério de utilidade da justificação do PCA"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_7_inv_2":
                msg = f"O processo {self.cod} é complementar de outro, no entanto a sua justificação não contém o critério de complementaridade informacional"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_6_inv_2":
                # FIXME: falta ver se isto não é redundante (rel_9_inv_3)
                if self.info:
                    msg = f"O processo {self.cod} é sintetizado por outro, mas o seu DF tem o valor de {self.info}, em vez de \"Eliminação\""
                else:
                    msg = f"O processo {self.cod} é sintetizado por outro e o valor do seu DF devia ser \"Eliminação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_5_inv_3":
                msg = f"O processo {self.cod} contém relações de \"eSuplementoDe\" no processo {self.info}. No entanto estes não são mencionados na justificação do PCA"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_9_inv_2":
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\", mas tem o valor de DF de {self.info}, em vez de \"Conservação\""
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_3_inv_1":
                # TODO: imprimir a lista melhor
                msg = f"O processo {self.cod} tem desdobramento, mas os seus filhos ({self.info["filhos"]}) têm valores de PCA e DF iguais ({self.info["valor"]})"
            case "rel_3_inv_5":
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
            case "rel_3_inv_7":
                msg = f"O processo {self.cod} tem uma relação de \"complementar de\" com o processo {self.info["proc"]} e nenhum dos filhos ({self.info["filhos"]}) tem um valor de DF de \"Conservação\""
            case "rel_3_inv_4":
                msg = f"Os termo {self.info["termo"]} do processo {self.cod} não foi replicado para o seu filho {self.info["filho"]}"
            case "rel_6_inv_3":
                msg = f"No processo {self.cod} não consta uma justificação com critério de densidade informacional"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_6_inv_4":
                msg = f"O processo {self.info} está em falta na justificação do DF do processo {self.cod}, sob o critério de densidade informacional"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_9_inv_3":
                # FIXME: falta ver se isto não é redundante (rel_6_inv_2)
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSintetizadoPor\", mas tem o valor de DF de {self.info}"
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSintetizadoPor\" e o valor do seu DF devia ser \"Eliminação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_7_inv_3":
                msg = f"O processo {self.info} está em falta na justificação do DF do processo {self.cod}, sob o critério de complementaridade informacional"
                if self.extra:
                    msg += f"({self.extra})"
                msg += "."
            case "rel_9_inv_1":
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eComplementarDe\", mas tem o valor de DF de {self.info}"
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eComplementarDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
            case "rel_4_inv_8":
                relacoes = ""
                # Aqui sabe-se que terá sempre mais que 1 elemento
                for rel in self.info["rels"][:-1]:
                    relacoes += f"{rel}, "
                relacoes += f"e {self.info["rels"][-1]}"
                msg = f"O processo {self.cod} tem mais do que uma relação ({relacoes}) com o processo {self.info["proc"]}"
            case "rel_6_inv_1":
                if self.info:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\", mas tem o valor de DF de {self.info}, em vez de \"Conservação\""
                else:
                    msg = f"O processo {self.cod} contém uma relação de \"eSinteseDe\" e o valor do seu DF devia ser \"Conservação\", mas neste caso o processo nem tem DF"
                msg += "."
            case "rel_4_inv_1_0":
                msg = f"O processo {self.cod} não é transversal, foram encontrados participantes associados a ele."
            case "rel_4_inv_3":
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_4":
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_5":
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_6":
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_2":
                msg = f"Foram encontradas as relações \"{self.cod} {self.info["rel"]} {self.info["c"]}\" e \"{self.info["c"]} {self.info["rel"]} {self.cod}\". Estas duas relações não podem existir em simultâneo."
            case "rel_4_inv_10":
                # TODO: indexar por termo??
                msg = f"O termo {self.info["t"]} foi encontrado repetido nos seguintes processos {self.info["cods"]}"
            case "rel_4_inv_7":
                msg = f"O processo {self.cod} relaciona-se com ele próprio, através da relação {self.info}"
            case "rel_8_inv_1":
                msg = f"No DF do processo {self.cod} foi encontrado uma justificação do tipo {self.info}"
            case "rel_4_inv_14":
                msg = f"O processo {self.cod} é transversal, mas não tem participantes"
            case "rel_3_inv_9":
                msg = f"O processo {self.info} está em harmonização, no entanto o seu filho {self.cod} está ativo."
            case _:
                pass
        return msg

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__
