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
            match inv:
                case "rel_2_inv_1":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_2_inv_2":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_2_inv_3":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_3_inv_1":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_3_inv_4":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_3_inv_5":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_3_inv_6":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_3_inv_7":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_4_inv_2":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_4_inv_3":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_4_inv_4":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_4_inv_5":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_4_inv_6":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1][0]} {i[1][1]}" for i in info])}")
                case "rel_4_inv_8":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_4_inv_11":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_5_inv_2":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_6_inv_2":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_8_inv_1":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")
                case "rel_9_inv_2":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} {i[1]}" for i in info])}")

                case _:
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")


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
        return ""

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__
