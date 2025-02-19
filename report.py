import json

class Report:

    def __init__(self):
        self.declaracoes = {} # {"100":["100.ttl"], "200":["100.ttl","200.ttl"]}
        self.missingRels = {
            "relsSimetricas": [],
            "relsInverseOf": []
        }
        self.globalErrors = {
            "struct":{
                "declsRepetidas": {}, # {"200":["100.ttl","200.ttl"]}
                "relsInvalidas": {} # {"200":["100.10.001","eCruzadoCom"]} -> "200" é mencionado por "100.10.001"
            },
            "outros": {}, # {"200": ["mensagem de erro"]}
            "erroInv":{}
        }
        self.warnings = {}


    def addErro(self,cod,msg):
        # TODO: criar hierarquia de erros
        if cod in self.globalErrors["outros"]:
            self.globalErrors["outros"][cod].append(msg)
        else:
            self.globalErrors["outros"][cod] = [msg]


    def addMissingRels(self,proc,rel,cod,tipo):
        # O "triplo" proc :rel cod está em falta
        self.missingRels[tipo].append((proc,rel,cod))


    def fixMissingRels(self,allClasses):

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
        relacoes = self.globalErrors["struct"]["relsInvalidas"]
        if proRel in relacoes:
            relacoes[proRel].append((cod,rel,tipoProcRef))
        else:
            relacoes[proRel] = [(cod,rel,tipoProcRef)]


    def checkStruct(self):
        ok = True
        repetidas = [(k,v) for k,v in self.declaracoes.items() if len(v)>1]
        if repetidas:
            self.globalErrors["struct"]["declsRepetidas"] = repetidas
            ok = False

        if len(self.globalErrors["struct"]["relsInvalidas"])>0:
            ok = False

        return ok


    def addFalhaInv(self,inv,s,p=None,o=None):

        if inv in self.globalErrors["erroInv"]:
            self.globalErrors["erroInv"][inv].append((s, p, o))
        else:
            self.globalErrors["erroInv"][inv] = [(s, p, o)]


    def addWarning(self,tipo,msg):

        match tipo:
            case "I":
                if "inferencias" in self.warnings:
                    self.warnings["inferencias"].append(f"{msg[0]} :{msg[1]} {msg[2]}")
                else:
                    self.warnings["inferencias"] = [f"{msg[0]} :{msg[1]} {msg[2]}"]
            case "H":
                if "harmonizacao" in self.warnings:
                    self.warnings["harmonizacao"].append(msg)
                else:
                    self.warnings["harmonizacao"] = [msg]
            case "R":
                if "relHarmonizacao" in self.warnings:
                    self.warnings["relHarmonizacao"].append(msg)
                else:
                    self.warnings["relHarmonizacao"] = [msg]

            case _:
                if "outro" in self.warnings:
                    self.warnings["outro"].append(msg)
                else:
                    self.warnings["outro"] = [msg]


    def printInv(self):

        for inv,info in self.globalErrors["erroInv"].items():
            print(f"\n{inv} ({len(info)}):\n")
            match inv:
                case "rel_4_inv_0":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_1_1":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_1_2":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_2":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_3":
                    print(f"\t- {"\n\t- ".join([f"{i[0]} :{i[1]} {i[2]}" for i in info])}")
                case "rel_4_inv_4":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_5":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_4_inv_6":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_2_inv_1":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_2_inv_2":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_2_inv_3":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_9_inv_2":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_3_inv_1":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case "rel_3_inv_5":
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")
                case _:
                    print(f"\t- {"\n\t- ".join([str(i[0]) for i in info])}")


    def dumpReport(self,dumpFileName="dump.json"):
        report = {}
        report["globalErrors"] = self.globalErrors
        report["warnings"] = self.warnings

        with open(f"dump/{dumpFileName}",'w') as f:
            json.dump(report,f,ensure_ascii=False, indent=4)
