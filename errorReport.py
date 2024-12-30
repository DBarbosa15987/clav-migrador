class ErrorReport:

    def __init__(self):
        self.struct = {
            "declaracoes": {}, # {"100":["100.ttl"], "200":["100.ttl","200.ttl"]}
            "relacoes": {} # {"200":["100.10.001","eCruzadoCom"]} -> "200" é mencionado por "100.10.001"
        }
        self.structOk = False
        self.invsOk = False
        self.globalErrors = {"struct":{},"erroInv":{}}
        self.erroInv = {}
        self.warnings = {}


    # def clear(self):
    #     self.struct = {"declaracoes": {}, "relacoes": {}}
    #     self.structOk = False
    #     self.invsOk = False
    #     self.erroInv = {}
    #     self.warnings = {}


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
        
        print(f"repetidas:{repetidas}")
        print("relsInvalidas:\n")
        print("\n".join([str(x) for x in relsInvalidas]))

        return ok


    def addFalhaInv(self,inv,s,p=None,o=None,title=""):

        if inv in self.erroInv:
            self.erroInv[inv].append((s, p, o))
        else:
            self.erroInv[inv] = [(s, p, o)]
