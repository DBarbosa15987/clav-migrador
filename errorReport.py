import json

class ErrorReport:

    def __init__(self):
        self.struct = {
            "declaracoes": {}, # {"100":["100.ttl"], "200":["100.ttl","200.ttl"]}
            "relacoes": {} # {"200":["100.10.001","eCruzadoCom"]} -> "200" é mencionado por "100.10.001"
        }
        self.globalErrors = {"struct":{},"erroInv":{}}
        self.erroInv = {}
        self.warnings = {}


    def addDecl(self,cod,fileName):
        # "cod" aparece declarado repetidamente no(s) ficheiro(s) set(declaracoes[cod])
        declaracoes = self.struct["declaracoes"]
        if cod in declaracoes:
            declaracoes[cod].append(fileName+".ttl")
        else:
            declaracoes[cod] = [fileName+".ttl"]


    def addRelacao(self,proRel,rel,cod,tipoProcRef=None):
        # "cod" é mencionado por relacoes[cod]
        relacoes = self.struct["relacoes"]
        if proRel in relacoes:
            relacoes[proRel].append((cod,rel,tipoProcRef))
        else:
            relacoes[proRel] = [(cod,rel,tipoProcRef)]


    def evalStruct(self):

        ok = True
        repetidas = [(k,v) for k,v in self.struct["declaracoes"].items() if len(v)>1]
        relsInvalidas = [(k,v,len(self.struct["relacoes"][k])) for k,v in self.struct["relacoes"].items() if k not in self.struct["declaracoes"]]

        if repetidas:
            self.globalErrors["struct"]["repetidas"] = repetidas
            ok = False
        if relsInvalidas:
            self.globalErrors["struct"]["relsInvalidas"] = relsInvalidas
            ok = False
        
        return ok


    def addFalhaInv(self,inv,s,p=None,o=None):

        if inv in self.erroInv:
            self.erroInv[inv].append((s, p, o))
        else:
            self.erroInv[inv] = [(s, p, o)]


    def printInv(self):

        for inv,info in self.erroInv.items():
            print(f"\n{inv}:\n")
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
        with open(f"dump/{dumpFileName}",'w') as f:
            json.dump(self.erroInv,f,ensure_ascii=False, indent=4)
