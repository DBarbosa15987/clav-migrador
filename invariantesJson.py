import json

sheets = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']

# {
#     "idInv": "rel_4_inv_0",
#     "desc": "Um processo sem desdobramento ao 4º nível tem de ter uma justificação associada ao PCA",
#     "query": "PREFIX : <http://jcr.di.uminho.pt/m51-clav#>\nselect * where {\n\t?s rdf:type :Classe_N3 .\nminus {\n\t?s :temPCA ?pca .\n\t?pca :temJustificacao ?j\n}\nminus{\n\t?x :temPai ?s\n}\n}"
# }

allErros = []

def rel_4_inv_0(file):
    """
    A função devolve as classes que não cumprem
    com este invariante:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA."
    """
    with open(file,'r') as f:
        sheet = json.load(f)
    classesN3 = [x for x in sheet if x["nivel"] == 3]
    erros = []
    for classe in classesN3:
        filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
        # Se não tem filhos tem de ter uma justificação associada ao PCA
        if len(filhos) == 0:
            if classe.get("pca"):
                if not classe["pca"].get("justificacao"):
                    erros.append(classe["codigo"])
            else:
                erros.append(classe["codigo"])
    print(erros)
    global allErros
    allErros += erros
    return erros

for sheet in sheets:
    rel_4_inv_0(f"files/{sheet}.json")
