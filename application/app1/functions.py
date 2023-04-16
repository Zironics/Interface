import os
import networkx as nx
from pattern.en import conjugate,lemma
import xml.etree.ElementTree as ET
import csv
from .centrality import *
app_directory = os.path.dirname(os.path.dirname( __file__ ))
    
#djad part : 


#def object_name(G,k): return G.nodes[k]['xml_obj'].findtext('./name')
def object_name(G,k): return G.nodes[k]['name']
#def attributes(G,k): return [attribute.findtext('.') for attribute in G.nodes[k]['xml_obj'].findall('./attributes/attribute')]
def attributes(G,k): return G.nodes[k]['attributes']
def relation_name(G,subject_id,object_id) -> str: return G.edges[(subject_id,object_id)]['predicate']
def draw(G): return nx.draw_networkx(G,labels={k:object_name(G,k) for k in G.nodes})
def captions(image_id): return [x.findtext('.') for x in ET.parse(f'./image_data/{image_id}').findall('./captions/caption')]

def extend_nodes(G,T,key=None):
    """
    G:Graph source (ses noeuds doivent contenir key dans leur dict)
    T:Graph distination 
    """
    for node in T.nodes:
        if key:
            T.nodes[node][key] = G.nodes[node][key]
        else:
            for k,v in G.nodes[node].items():
                T.nodes[node][k] = v

def extend_edges(G,T,key=None):
    """
    G:Graph source (ses edges doivent contenir key dans leur dict)
    T:Graph distination 
    """
    for edge in T.edges:
        if key:
            T.edges[edge][key] = G.edges[edge][key]
        else:
            for k,v in G.edges[edge].items():
                T.edges[edge][k] = v
        
def leaves(T:nx.DiGraph):
    return [node for node in T.nodes if node != T.graph['root'] and T.degree[node] == 1 ]

def rev(l:list) -> list:
    r = l.copy()
    r.reverse()
    return r


def extraire_arbre(Cluster:nx.DiGraph) -> nx.DiGraph: 
    T = nx.Graph()
    T.add_nodes_from([node for node in Cluster.nodes(data=True)])
    T.add_edges_from(sorted([edge for edge in Cluster.edges(data=True)],reverse=True,key=lambda e:e[2]['weight']))

    arbre = nx.minimum_spanning_tree(T)
    T = nx.minimum_spanning_tree(T)
    
    if arbre.number_of_nodes() <= 1:
        T.graph['root'] = Cluster.graph['Central_node']
        arbre.graph['root'] = T.graph['root']
        return arbre,arbre

    arbre = nx.DiGraph([e if e in Cluster.edges(data=True) else (e[1],e[0],e[2]) for e in arbre.edges(data=True)])
    
    extend_nodes(T,arbre)
    extend_edges(T,arbre)

    T.graph['root'] = Cluster.graph['Central_node']
    arbre.graph['root'] = T.graph['root']
    
    return arbre,T

def getEdge(G:nx.DiGraph,u,v,data=False) :
    """"
    retourner l'arc existant entre u,v ou v,u
    """

    if G.has_edge(u,v):
        return (u,v) if not data else (u,v,G.edges[u,v])
    elif G.has_edge(v,u):
        return (v,u) if not data else (v,u,G.edges[v,u])
    
def has_execluded_predicate(G,path,execluded):
    for i in range(len(path)):
        if i>0 and relation_name(G,*getEdge(G,path[i-1],path[i])) in execluded:
            return True
    return False


from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from pattern.text.en import conjugate,lemma,tenses,article,singularize

execluded = [
'has',
'OF',
'with',
'has a',
'of a',
'have',
'of',
'along',
]

def sentence(image_id:str,method:str,seuil:float,nb_obj:int,nb_rel:int,nb_attr:int) -> str:    
    G = CreateGraph(image_id,nb_obj,nb_rel,nb_attr)
    Cluster = centrality_cluster(G,seuil,method)
    
    if not Cluster:
        print("Cluster vide")
        return
    print(Cluster.nodes(data=True))
    
    OT,UT = extraire_arbre(Cluster)

    root = OT.graph['root']

    phrase = article(attributes(OT,root)[0] if attributes(OT,root) else object_name(OT,root)) + ' ' 
    phrase += ' '.join(attributes(OT,root)) + ' ' + object_name(OT,root) if attributes(OT,root) else object_name(OT,root)
    pos = []
    neg = []

    for leaf in leaves(OT):
        path = nx.shortest_path(UT,root,leaf)
        
        #if len(path) - 1 > 4:
        #    print("La profondeur 4 est atteinte :",path)
        #    continue
        
        pluriel = 'singular'
        if nx.is_path(OT,path):

            pos_flow = ""
            first = True
            for i in range(1,len(path)):
                
                if relation_name(OT,path[i-1],path[i]) in execluded: 
                    continue

                if singularize(object_name(OT,path[i-1])) != object_name(OT,path[i-1]):
                    pluriel = 'plural' 

                if pos_tag(word_tokenize(relation_name(OT,path[i-1],path[i]).lower()),tagset='universal')[0][-1] == 'ADP': # le predicat est un preposition
                    verb =  ' ' + conjugate('be','present',3,pluriel) + ' ' + relation_name(OT,path[i-1],path[i]).lower()

                elif pos_tag(word_tokenize(relation_name(OT,path[i-1],path[i])),tagset='universal')[0][-1] == 'VERB':
                    if tenses(relation_name(OT,path[i-1],path[i]))[0][-1] == 'progressive':
                        verb =  ' ' + conjugate('be','present',3,pluriel) + ' ' + relation_name(OT,path[i-1],path[i]).lower()
                    else:
                        verb = ' ' + conjugate(lemma(relation_name(OT,path[i-1],path[i])),'present',3,pluriel)
                else:
                    verb = ' ' + relation_name(OT,path[i-1],path[i]).lower()


                pos_flow += verb if first else ' that' + verb

                attribute = attributes(OT,path[i])
                pos_flow += ' ' + article(attribute[0] if attribute else object_name(OT,path[i])) + ' '
                pos_flow += ' '.join(attribute) + ' ' + object_name(OT,path[i]) if attribute else object_name(OT,path[i])

                first = False
                pluriel = 'singular'


            if pos_flow:
                pos.append(pos_flow)

        elif nx.is_path(OT,rev(path)):
            path = rev(path)
            neg_flow = ""
            last = False
            for i in range(len(path)-1): 

                if relation_name(OT,path[i],path[i+1]) in execluded:
                    if i == len(path) - 2:
                        last = True
                    continue 

                if singularize(object_name(OT,path[i])) != object_name(OT,path[i]):
                    pluriel = 'plural' 

                if pos_tag(word_tokenize(relation_name(OT,path[i],path[i+1])),tagset='universal')[0][-1] == 'VERB' \
                    and not (tenses(relation_name(OT,path[i],path[i+1]))[0][-1] == 'progressive' or tenses(relation_name(OT,path[i],path[i+1]))[0][0] == 'infinitive'):
                        verb = ' ' + conjugate(lemma(relation_name(OT,path[i],path[i+1]).lower()),'present',3,pluriel,aspect='progressive')
                else:
                    verb = ' ' + relation_name(OT,path[i],path[i+1]).lower()


                attribute = attributes(OT,path[i])
                neg_flow += ' ' + article(attribute[0] if attribute else object_name(OT,path[i])) + ' '
                neg_flow += ' '.join(attribute) + ' ' + object_name(OT,path[i]) if attribute else object_name(OT,path[i])

                neg_flow += verb if i!= len(path) - 2 else ' ' + conjugate('be','present',3,pluriel) + verb
                
                if i == len(path) - 2:
                    last = True
                pluriel = 'singular'
                    
            if neg_flow:       
                if not last:
                    neg_flow += ' it' 
                neg.append(neg_flow)

        else:
            pass
            #print('not flow')
            #print([object_name(OT,x) for x in path])
            #for i  in range(len(path)-1):
            #    s,o = getEdge(OT,path[i],path[i+1])
            #    print(object_name(OT,s),relation_name(OT,s,o),object_name(OT,o),sep=' ',end='\t')
    

    if pos and neg:
        phrase = phrase + " which" + ' and'.join(neg) + ',' + ' and'.join(pos) 
    elif neg:
        phrase = "There is " + phrase + " which" + ' it and'.join(neg) + ' it'
    elif pos:
        phrase = phrase + ' and'.join(pos)
    else:
        phrase = 'There is ' + phrase
        
    return phrase.capitalize()