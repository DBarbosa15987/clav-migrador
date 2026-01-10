import re
from .report import Report
brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
sepExtra = re.compile(r'#$|^#')

def procContexto(classe, cod, myReg, entCatalog, tipCatalog, legCatalog, rep: Report):
    # Tipos de intervenção
    # --------------------------------------------------
    intervCatalog = ['Apreciar','Assessorar','Comunicar','Decidir','Executar','Iniciar']
    # --------------------------------------------------
    if classe["Dimensão qualitativa do processo"]:
        myReg["dimensao"] = classe["Dimensão qualitativa do processo"]
    if classe["Uniformização do processo"]:
        myReg["uniformizacao"] = classe["Uniformização do processo"]
    # Tipo de processo -----
    if classe["Tipo de processo"]:
        myReg['tipoProc'] = brancos.sub('', str(classe["Tipo de processo"]))
        if myReg["estado"]!='H' and myReg['tipoProc'] not in ['PC','PE']:
            rep.addErro(cod,f"Tipo de processo desconhecido::<b>{myReg['tipoProc']}</b>")
        elif myReg["estado"]!='H' and myReg['tipoProc'] == '':
            rep.addErro(cod,f"Tipo de processo não preenchido::<b>{myReg['tipoProc']}</b>")
    # Transversalidade -----
    if classe["Processo transversal (S/N)"]:
        myReg['procTrans'] = brancos.sub('', classe["Processo transversal (S/N)"])
        if myReg["estado"]!='H' and myReg['procTrans'] not in ['S','N']:
            rep.addErro(cod,f"Transversalidade desconhecida::<b>{myReg['procTrans']}</b>")
    elif myReg["estado"]!='H' and myReg["nivel"] == 3:
        rep.addErro(cod,"Não tem transversalidade preenchida")
    # Donos -----
    if classe["Dono do processo"]:
        donos = brancos.sub('', classe["Dono do processo"])
        donos = sepExtra.sub('', donos)
        listaDonos = donos.split('#')
        ldonos = []
        for d in listaDonos:
            limpo = brancos.sub('', d)
            novo = re.sub(r'[ \u202F\u00A0]+', '_', limpo)
            ldonos.append(novo)
        myReg['donos'] = ldonos
        # ERRO: Verificação da existência dos donos no catálogo de entidades e/ou tipologias
        for d in myReg['donos']:
            if myReg['estado'] != 'H' and (d not in entCatalog) and (d not in tipCatalog):
                rep.addErro(cod,f"Entidade dono não está no catálogo de entidades ou tipologias::<b>{d}</b>")
        # ERRO: Um processo tem de ter sempre donos
        if myReg['estado'] != 'H' and len(myReg['donos']) == 0:
            rep.addErro(cod,"Este processo não tem donos identificados.")
    # Participantes -----
    if classe["Participante no processo"]:
        participantes = brancos.sub('', classe["Participante no processo"])
        participantes = sepExtra.sub('', participantes)
        lparticipantes = participantes.split('#')
        myReg['participantes'] = []
        for p in lparticipantes:
            limpa = brancos.sub('', p)
            myReg['participantes'].append({'id': re.sub(r'[ \u202F\u00A0]+', '_', limpa)})
        # ERRO: Verificação da existência dos participantes no catálogo de entidades e/ou tipologias
        for part in myReg['participantes']:
            if myReg['estado'] != 'H' and (part['id'] not in entCatalog) and (part['id'] not in tipCatalog):
                rep.addErro(cod,f"Entidade participante não está no catálogo de entidades ou tipologias::<b>{part['id']}</b>")
    # Tipo de intervenção -----
    linterv = []
    if classe["Tipo de intervenção do participante"]:
        interv = brancos.sub('', classe["Tipo de intervenção do participante"])
        interv = re.sub(r'[ ]+','',interv)
        interv = sepExtra.sub('', interv)
        linterv = interv.split('#')
        # ERRO: Verificação da existência do tipo de intervenção no catálogo de intervenções
        for i in linterv:
            if myReg["estado"]!='H' and i not in intervCatalog:
                rep.addErro(cod,f"Tipo de intervenção não está no catálogo de intervenções::<b>{i}</b>")
            # ERRO: Participantes e intervenções têm de ter a mesma cardinalidade
        if classe["Participante no processo"] and classe["Tipo de intervenção do participante"]:
            if myReg["estado"]!='H' and len(myReg['participantes']) != len(linterv):
                rep.addErro(cod,f"Participantes e intervenções não têm a mesma cardinalidade")
            elif len(myReg['participantes']) == len(linterv):
                for index, i in enumerate(linterv):
                    myReg['participantes'][index]['interv'] = i
            else:
                rep.addWarning(info={'msg':f"Processo <b>{cod}</b> em harmonização e participantes e intervenções não têm a mesma cardinalidade, estas não foram migradas"})
    # Legislação -----
    if classe["Diplomas jurídico-administrativos REF"]:
        leg = brancos.sub('', classe["Diplomas jurídico-administrativos REF"])
        leg = sepExtra.sub('', leg)
        myReg['legislacao'] = leg.split('#')
        nova =[]
        # Limpeza e normalização dos ids da legislação
        for l in myReg['legislacao']:
            limpa = re.sub(r'([ \u202F\u00A0]+)|([ \u202F\u00A0]*,[ \u202F\u00A0]*)', '_', brancos.sub('', l))
            limpa = re.sub(r'[/ \u202F\u00A0()\-\u2010]+', '_', limpa)
            nova.append(limpa)
        myReg['legislacao'] = nova
        # ERRO: Verificação da existência da legislação no catálogo legislativo
        for l in myReg['legislacao']:
            if myReg["estado"]!='H' and l not in legCatalog:
                rep.addErro(cod,f"Legislação inexistente no catálogo legislativo::<b>{l}</b>")
    # Processos Relacionados -----
    if classe["Código do processo relacionado"]:
        proc = brancos.sub('', classe["Código do processo relacionado"])
        proc = sepExtra.sub('', proc)
        processos = proc.split('#')
        limpos = []
        for proc in processos:
            limpo = brancos.sub('', proc)
            limpos.append(limpo)
        myReg['processosRelacionados'] = limpos
    # Tipo de relação entre processos -----
    if classe["Tipo de relação entre processos"]:
        procRel = brancos.sub('', classe["Tipo de relação entre processos"])
        procRel = sepExtra.sub('', procRel)
        myReg['proRel'] = procRel.split('#')
        # Normalização do tipo de relação
        normalizadas = []
        for rel in myReg['proRel']:
            if re.search(r'S[íi]ntese[ ]*\(s[ií]ntetizad[oa](\s+por)?\)', rel, re.I):
                normalizadas.append('eSintetizadoPor')
            elif re.search(r'S[íi]ntese[ ]*\(sintetiza\)', rel, re.I):
                normalizadas.append('eSinteseDe')
            elif re.search(r'Complementar', rel, re.I):
                normalizadas.append('eComplementarDe')
            elif re.search(r'\s*Cruzad', rel, re.I):
                normalizadas.append('eCruzadoCom')
            elif re.search(r'\s*Suplement.?\s*de', rel, re.I):
                normalizadas.append('eSuplementoDe')
            elif re.search(r'\s*Suplement.?\s*para', rel, re.I):
                normalizadas.append('eSuplementoPara')
            elif re.search(r'Sucessão[ ]*\(suce', rel, re.I):
                normalizadas.append('eSucessorDe')
            elif re.search(r'\s*Sucessão\s*\(antece', rel, re.I):
                normalizadas.append('eAntecessorDe')
            else:
                normalizadas.append(rel)
                if myReg["estado"]!='H':
                    rep.addErro(cod,f"Relação entre processos desconhecida::<b>{rel}</b>",grave=True)
            myReg['proRel'] = normalizadas

    # ERRO: Processos e Relações têm de ter a mesma cardinalidade
    if classe["Código do processo relacionado"] and classe["Tipo de relação entre processos"]:
        if myReg["estado"]!='H' and len(myReg['processosRelacionados']) != len(myReg['proRel']):
            rep.addErro(cod,"Processos relacionados e respetivas relações não têm a mesma cardinalidade",True)
