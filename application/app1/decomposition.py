import networkx as nx
from .centrality import *

app_directory = os.path.dirname(os.path.dirname( __file__ ))

def have_bidirectional_relationship(G, node1, node2):
    return G.has_edge(node1, node2) and G.has_edge(node2, node1)

def remove_bidirectional_edges(G):
    H = G.copy()
    biconnections = set()
    
    for u, v, *_ in H.edges():
        if int(u) > int(v):  # Avoid duplicates, such as (1, 2) and (2, 1)
            v, u = u, v
        if have_bidirectional_relationship(H, u, v):
            biconnections.add((u, v))

    for b in biconnections :
        v , u = b
        if H.get_edge_data(b[0],b[1])['weight'] > H.get_edge_data(b[1],b[0])['weight']:
            u , v = b
        H.remove_edge(u,v)
    return H


def process_clique(G):
    
    # si le graph est une clique on supprime la relation la moins partinente
    # c.a.d ayant le weight le plus grands
    
    H = G.copy()
    m = 0
    for node1,node2,data in H.edges(data = True):
        if data['weight'] >= m:
            u , v = node1 , node2
            m = data['weight']
    H.remove_edge(u,v)
    return H

def get_name(info):
    print("info :",info)
    return info['name']


def get_attributes(info):
    if 'attributes' in info :
        return info['attributes']
    return ""
def get_relation_binaire(l):
    for r in l:
        if r[0] != r[1]:
            return r

def get_predicat(subj,obj,edges):
    for e in edges:
        if e[0] == subj and e[1] == obj :
            return e[2]['predicate']
    return None

def is_clique(edges):
    # dans le cas d'un graph de taille 3 sinon sa ne marche pas
    return len(edges) >= 3

def graph_to_sentence(G,ancestors = False):
    predicate_to_exclude = ['has','wearing','has a','of','of a']
    # 1st case degree is 1 : 
    if G.number_of_nodes() == 1:
        attributes = get_attributes(list(G.nodes(data = True))[0][1])
        if attributes :
            attributes = " and ".join(attributes)
        else:
            attributes = ""
        node = get_name(list(G.nodes(data = True))[0][1])
        
        return " ".join(["a",attributes,node])
            
            
    elif G.number_of_nodes() == 2 :
        G = remove_bidirectional_edges(G)
        edges = get_relation_binaire(G.edges(data = True))
       
        attributes_subject = " ".join(get_attributes(G.nodes[edges[0]]))

        attributes_object = " ".join(get_attributes(G.nodes[edges[1]]))

            
        predicat = edges[2]['predicate']
        if predicat not in ['has','of','has a','of a'] and 'is ' not in predicat:
            predicat = 'is ' + predicat
        subject = get_name(G.nodes[edges[0]])
        obj = get_name(G.nodes[edges[1]])
        
        return " ".join(["a",attributes_subject,subject,predicat.lower(),"a",attributes_object,obj])
    
    elif G.number_of_nodes() == 3:
        G = remove_bidirectional_edges(G)
        degrees = {node:val for (node, val) in G.degree()} # dictionnaire de degree node -> degree
        edges = G.edges(data = True)
        
        if not is_clique(edges):
                
            # trouver le noed avec deg = 2 
            for key,deg in degrees.items():
                if deg == 2:
                    degree2 = key
                    break
            other_noeds = [x for x in degrees.keys() if x != degree2]


            
            # il ya trois cas(voir page 419 de la these):2 arcs entrants, 2 arcs sortant, 1 arc entrant 1 arc sortant
            
            # 1er cas 2 arcs entrants :
            # 3 cas, meme noms memes relation,meme ralations noms differents, relations differentes: 
            # si meme noms meme relations : 
           
            if  len(G.in_edges(degree2)) == 2:
                predicat0 = get_predicat(other_noeds[0],degree2,edges)
                predicat1 = get_predicat(other_noeds[1],degree2,edges)
                obj0 = get_name(G.nodes[other_noeds[0]])
                obj1 = get_name(G.nodes[other_noeds[1]])
                obj2 = get_name(G.nodes[degree2])
                
                if predicat0 not in ['has','of','has a','of a'] and 'is ' not in predicat0:
                    predicat0 = 'is ' + predicat0
                
                if predicat1 not in ['has','of','has a','of a'] and 'is ' not in predicat1:
                    predicat1 = 'is ' + predicat1                
                
                
                if (obj0 == obj1 and predicat0 == predicat1):
                    return " ".join(["two",obj0,predicat0.lower(),'a',obj2])
            
                # si meme relations noms different :
                
                if (obj0 != obj1 and predicat0 == predicat1):
                    return " ".join(["a",obj0,"and a",obj1,predicat0.lower(),obj2])
            
                # si relations differentes :
                elif (predicat0 != predicat1):
                    return " ".join(["a",obj0,predicat0.lower(),'a',obj2,'and a',obj1,predicat1.lower(),"that",obj2])
                
            # cas 2 sortants
            if  len(G.out_edges(degree2)) == 2:
                predicat0 = get_predicat(degree2,other_noeds[0],edges)
                predicat1 = get_predicat(degree2,other_noeds[1],edges)
                obj0 = get_name(G.nodes[other_noeds[0]])
                obj1 = get_name(G.nodes[other_noeds[1]])
                obj2 = get_name(G.nodes[degree2])
               
                if predicat0 not in ['has','of','has a','of a'] and 'is ' not in predicat0:
                    predicat0 = 'is ' + predicat0
                
                if predicat1 not in ['has','of','has a','of a'] and 'is ' not in predicat1:
                    predicat1 = 'is ' + predicat1
                    
                if (obj0 == obj1):
                    return " ".join(["a",obj2,"that",predicat0.lower(),'a',obj0,',',predicat1.lower(),"another",obj1])
            
                # si noms different :
                if (obj0 != obj1 ):
                    return " ".join(["a",obj2,"that",predicat0.lower(),'a',obj0,',',predicat1.lower(),"a",obj1])
            
            # cas 1 entrant 1 sortant : 
            if  len(G.out_edges(degree2)) == 1:
                
                predicat0 = get_predicat(other_noeds[0],degree2,edges)
                if predicat0:
                    predicat1 = get_predicat(degree2,other_noeds[1],edges)
                    obj0 = get_name(G.nodes[other_noeds[0]])
                    obj1 = get_name(G.nodes[other_noeds[1]])
                else :
                    predicat1 = get_predicat(degree2,other_noeds[0],edges)
                    predicat0 = get_predicat(other_noeds[1],degree2,edges)
                    obj1 = get_name(G.nodes[other_noeds[0]])
                    obj0 = get_name(G.nodes[other_noeds[1]])
                
                if predicat0 not in ['has','of','has a','of a'] and 'is ' not in predicat0:
                    predicat0 = 'is ' + predicat0
                
                if predicat1 not in ['has','of','has a','of a'] and 'is ' not in predicat1:
                    predicat1 = 'is ' + predicat1
                obj2 = get_name(G.nodes[degree2])
                
                if (obj0 == obj1):
                    return " ".join(["a",obj0,predicat0.lower(),'a',obj2,'that',predicat1.lower(),"another",obj1])
                    
                # si noms different :
                if (obj0 != obj1 ):
                    return " ".join(["a",obj0,predicat0.lower(),'a',obj2,'that',predicat1.lower(),"a",obj1])
                
        else : 
            H = process_clique(G)
            return (graph_to_sentence(H))
        
    else : # graph de taille superieur a 3
        G = remove_bidirectional_edges(G)
        
        central_node = str(G.graph['Central_node'])
        
        i = 1 if ancestors else 0
        j = 0 if ancestors else 1
        
        

        nodes = set()
        edges = []

        for x in G.edges(data = True):
            if x[2]['predicate'] not in predicate_to_exclude:
               nodes.add(x[1])
               nodes.add(x[0])
               edges.append((x[0],x[1]))

        if len(nodes) != 1 and len(nodes)<4:
            H = G.edge_subgraph(edges)
            return graph_to_sentence(H)
        else :
            edges = []
            found = False
            for x in G.edges(data = True):
                if x[i] == central_node and x[2]['predicate'].lower() not in predicate_to_exclude:
                    found = True
                    edges.append((x[0],x[1]))
                    
                    if G.out_degree(x[j]) != 0:
                        found = False
                        for y in G.edges(data = True):
                            if y[0] == x[j] and y[2]['predicate'].lower() not in predicate_to_exclude:
                                edges.append((y[0],y[1]))
                                found = True
                                break
                                
                        if not found :
                            for y in G.edges(data = True):
                                if y[0] == x[j]:
                                    found = True
                                    edges.append((y[0],y[1]))
                                    break
                    break
                    
            if not found:
                for x in G.edges(data = True):
                    if x[i] == central_node:
                        edges.append((x[0],x[1]))
                        break
            print("edges:",edges)
            H = G.edge_subgraph(edges)
            return graph_to_sentence(H)
        

def generate_sentence(image_id,method,nb_obj,nb_rel,nb_att,seuil):

    G = CreateGraph(image_id,nb_obj,nb_rel,nb_att)
    Cluster = centrality_cluster(G,seuil,method)
    
    print(Cluster.graph)
    if Cluster.number_of_nodes() <= 3 :
        sentence = graph_to_sentence(Cluster)
    else :
        des = list(nx.descendants(Cluster, Cluster.graph['Central_node']))
        if len(des) != 0 :
            des.append(Cluster.graph['Central_node'])
            Cluster = Cluster.subgraph(des)
            sentence = graph_to_sentence(Cluster)

        else :
            anc = list(nx.ancestors(Cluster, Cluster.graph['Central_node']))
            anc.append(Cluster.graph['Central_node'])
            Cluster = Cluster.subgraph(anc)
            sentence = graph_to_sentence(Cluster, ancestors = True)
    
    img = ET.parse(os.path.join(app_directory, f'image_data/{image_id}')).getroot()
    for cap in img.iter('caption'):
        print("caption : ",cap.text)
    print("result : ", sentence)
    return sentence