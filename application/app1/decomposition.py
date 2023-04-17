import networkx as nx
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from .centrality import *
from pattern.en import singularize,pluralize,conjugate

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

def isplural(pluralForm):
    try :
        singularForm = singularize(pluralForm)
    except :
        return False
    plural = True if pluralForm is not singularForm else False
    return plural

def traiter_predicat(subject,predicat):
    a = predicat.split(" ")[0]
    if a in ['are',"is"]:
        predicat = " ".join(predicat.split(' ')[1:])
    
    if predicat in ['has','has a','of','with','of a']:
        return predicat
    
    elif isplural(subject):
        return " ".join(["are",predicat])
    else :
        return " ".join(["is",predicat])
    


def selection_determinant(subject,attribut):
    vowels = ["a","e","i","o","u"]
    if attribut != "":
        if attribut[0].lower() in vowels:
            return 'an'
        else :
            return 'a'
    else :
        # cas det = a
        if not isplural(subject):
            if subject[0].lower() in vowels:
                return 'an'
            else :
                return 'a'
        #cas det = some
        else :
            return 'some'

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

def choose_edge_for_node(G,node,exclude = []):
    predicate_to_exclude = ['wearing','has','has a','of','of a']
    if len(G.out_edges(node)) > 0:
        for x in G.out_edges(node,data = True):
            if x[2]['predicate'].lower() not in predicate_to_exclude and x[1] not in exclude:
                return (x[0],x[1])

        for p in predicate_to_exclude:
            for x in G.out_edges(node,data = True):
                if x[2]['predicate'].lower() == p and x[1] not in exclude:
                    return (x[0],x[1])
    elif len(G.in_edges(node)) > 0:
        for x in G.in_edges(node,data = True):
            if x[2]['predicate'].lower() not in predicate_to_exclude and x[0] not in exclude:
                return (x[0],x[1])

        for p in predicate_to_exclude:
            for x in G.in_edges(node,data = True):
                if x[2]['predicate'].lower() == p and x[0] not in exclude:
                    return (x[0],x[1])
    else :
        return None

def choose_two_edges(G,central):
    predicate_to_exclude = ['wearing','has','has a','of','of a']
    edges = []
    if len(G.out_edges(central)) > 0:
        if len(G.out_edges(central)) == 1:
            e1 = list(G.out_edges(central))[0]
            edges.append(e1)
            e2 = choose_edge_for_node(G,e1[1],exclude=[central])
            if e2 != None :
                edges.append(e2)
            # verifier les ancestre sinon
            return edges
        
        elif len(G.out_edges(central)) == 2:
            edges = G.out_edges(central)
            return edges
        else :
            for x in G.out_edges(central,data = True):
                print("predicate : ",x)
                if x[2]['predicate'].lower() not in predicate_to_exclude:
                    edges.append(x)
            if len(edges) == 2:
                return [(edges[0][0],edges[0][1]),(edges[1][0],edges[1][1])]
            
            elif len(edges) > 2:
                if edges[0][2]["weight"] >= edges[1][2]["weight"]:
                    m1 = edges[0]
                    m2 = edges[1]
                else :
                    m1 = edges[1]
                    m2 = edges[0]
                
                for i in range(2,len(edges)):
                    w = edges[i][2]["weight"]
                    if w > m2[2]["weight"]:
                        if w > m1[2]["weight"]:
                            m1 = edges[i]
                        else :
                            m2 = edges[i]
                return [(m1[0],m1[1]),(m2[0],m2[1])]
            elif len(edges) == 1:
                found = False
                edges = [(edges[0][0],edges[0][1])]
                for p in predicate_to_exclude:
                    for x in G.out_edges(central,data = True):
                        if x[2]['predicate'].lower() == p:
                            edges.append((x[0],x[1]))
                            found = True
                            break
                    if found : break
                return edges
            else : #0
                for p in predicate_to_exclude:
                    for x in G.out_edges(central,data = True):
                        if x[2]['predicate'].lower() == p:
                            edges.append((x[0],x[1]))
                            if len(edges) == 2:
                                return edges
    elif len(G.in_edges(central)) > 0:
        print("in edges")
        if len(G.in_edges(central)) == 1:
            e1 = list(G.in_edges(central))[0]
            edges.append(e1)
            e2 = choose_edge_for_node(G,e1[0],exclude=[central])
            if e2 != None :
                edges.append(e2)
            # verifier les ancestre sinon
            return edges
        
        elif len(G.in_edges(central)) == 2:
            edges = G.in_edges(central)
            return edges
        
        else :
            for x in G.in_edges(central,data = True):
                if x[2]['predicate'].lower() not in predicate_to_exclude:
                    edges.append(x)
            if len(edges) == 2:
                return [(edges[0][0],edges[0][1]),(edges[1][0],edges[1][1])]
            
            elif len(edges) > 2:
                if edges[0][2]["weight"] >= edges[1][2]["weight"]:
                    m1 = edges[0]
                    m2 = edges[1]
                else :
                    m1 = edges[1]
                    m2 = edges[0]
                
                for i in range(2,len(edges)):
                    w = edges[i][2]["weight"]
                    if w > m2[2]["weight"]:
                        if w > m1[2]["weight"]:
                            m1 = edges[i]
                        else :
                            m2 = edges[i]
                return [(m1[0],m1[1]),(m2[0],m2[1])]
            elif len(edges) == 1:
                edges = [(edges[0][0],edges[0][1])]
                for p in predicate_to_exclude:
                    for x in G.in_edges(central,data = True):
                        if x[2]['predicate'].lower() == p:
                            edges.append((x[0],x[1]))
                            break
                return edges
            else : #0
                for p in predicate_to_exclude:
                    for x in G.in_edges(central,data = True):
                        if x[2]['predicate'].lower() == p:
                            edges.append((x[0],x[1]))
                            if len(edges) == 2:
                                return edges

def graph_to_sentence(G):
    predicate_to_exclude = ['has','wearing','has a','of','of a']
    # 1st case degree is 1 : 
    if G.number_of_nodes() == 1:
        attributes = get_attributes(list(G.nodes(data = True))[0][1])
        if attributes != "" :
            attributes = " and ".join(attributes)
        else:
            attributes = ""
        node = get_name(list(G.nodes(data = True))[0][1])

        det = selection_determinant(node,attributes)
        
        return " ".join([det,attributes,node])
            
            
    elif G.number_of_nodes() == 2 :
        G = remove_bidirectional_edges(G)
        edges = get_relation_binaire(G.edges(data = True))
       
        attributes_subject = " and ".join(get_attributes(G.nodes[edges[0]]))

        attributes_object = " and ".join(get_attributes(G.nodes[edges[1]]))

            
        predicat = edges[2]['predicate']
        
        subject = get_name(G.nodes[edges[0]])
        obj = get_name(G.nodes[edges[1]])

        predicat = traiter_predicat(subject,predicat)

        dets = selection_determinant(subject,attributes_subject)
        deto = selection_determinant(obj,attributes_object)
        
        return " ".join([dets,attributes_subject,subject,predicat.lower(),deto,attributes_object,obj])
    
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
           
            if  len(G.in_edges(degree2)) == 2:
                predicat0 = get_predicat(other_noeds[0],degree2,edges)
                predicat1 = get_predicat(other_noeds[1],degree2,edges)
                obj0 = get_name(G.nodes[other_noeds[0]])
                obj1 = get_name(G.nodes[other_noeds[1]])
                obj2 = get_name(G.nodes[degree2])

                attributes_obj0 = " and ".join(get_attributes(G.nodes[other_noeds[0]])) 
                attributes_obj1 = " and ".join(get_attributes(G.nodes[other_noeds[1]])) 
                attributes_obj2 = " and ".join(get_attributes(G.nodes[degree2])) 

                det0 = selection_determinant(obj0,attributes_obj0)
                det1 = selection_determinant(obj1,attributes_obj1)
                det2 = selection_determinant(obj2,attributes_obj2)

                
                # 3 cas, meme noms memes relation,meme ralations noms differents, relations differentes: 
                # si meme noms meme relations : 
                if (obj0 == obj1 and predicat0 == predicat1):
                    try :
                        obj0 = pluralize(obj0)
                    except:
                        pass

                    predicat0 = traiter_predicat(obj0,predicat0)

                    return " ".join(["two",obj0,predicat0.lower(),det2,attributes_obj2,obj2])
            
                # si meme relations noms different :
                
                if (obj0 != obj1 and predicat0 == predicat1):
                    predicat0 = traiter_predicat(obj0,predicat0)
                    
                    return " ".join([det0,attributes_obj0,obj0,"and",det1,attributes_obj1,obj1,predicat0.lower(),det2,attributes_obj2,obj2])
            
                # si relations differentes :
                elif (predicat0 != predicat1):
                    predicat0 = traiter_predicat(obj0,predicat0)
                    predicat1 = traiter_predicat(obj1,predicat1)

                    return " ".join([det0,attributes_obj0,obj0,predicat0.lower(),det2,attributes_obj2,obj2,'and',det1,
                                    attributes_obj1,obj1,predicat1.lower(),"the same",obj2])
                
            # cas 2 sortants
            if  len(G.out_edges(degree2)) == 2:
                predicat0 = get_predicat(degree2,other_noeds[0],edges)
                predicat1 = get_predicat(degree2,other_noeds[1],edges)
                obj0 = get_name(G.nodes[other_noeds[0]])
                obj1 = get_name(G.nodes[other_noeds[1]])
                obj2 = get_name(G.nodes[degree2])

                attributes_obj0 = " and ".join(get_attributes(G.nodes[other_noeds[0]])) 
                attributes_obj1 = " and ".join(get_attributes(G.nodes[other_noeds[1]])) 
                attributes_obj2 = " and ".join(get_attributes(G.nodes[degree2]))
                
                det0 = selection_determinant(obj0,attributes_obj0)
                det1 = selection_determinant(obj1,attributes_obj1)
                det2 = selection_determinant(obj2,attributes_obj2)

                print(predicat0,predicat1)
                if pos_tag(word_tokenize(predicat0),tagset='universal')[0][-1] == 'VERB':
                    predicat0 = conjugate(lemma(predicat0.lower()),tense = "present",mood ="indicative",aspect = "progressive")
                if pos_tag(word_tokenize(predicat0),tagset='universal')[0][-1] == 'VERB':
                    predicat1 = conjugate(lemma(predicat1.lower()),tense = "present",mood ="indicative",aspect = "progressive")

                predicat0 = traiter_predicat(degree2,predicat0).lower()
                predicat1 = traiter_predicat(degree2,predicat1).lower()
                
                if (obj0 == obj1):
                    return " ".join([det2,attributes_obj2,obj2,"that",predicat0.lower(),det0,attributes_obj0,obj0,',',
                                    predicat1.lower(),"another",attributes_obj1,obj1])
            
                # si noms different :
                if (obj0 != obj1 ):
                    return " ".join([det2,attributes_obj2,obj2,"that",predicat0,det0,attributes_obj0,obj0,',',predicat1,
                                det1,attributes_obj1,obj1])
            
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
        
        edges = choose_two_edges(G,central_node)
        print("edges:",edges)
        H = G.edge_subgraph(edges)
        return graph_to_sentence(H)
        

def generate_sentence(image_id,method,nb_obj,nb_rel,nb_att,seuil):

    G = CreateGraph(image_id,nb_obj,nb_rel,nb_att)
    Cluster = centrality_cluster(G,seuil,method)
    
    print(Cluster.graph)
    print(Cluster.edges())
    sentence = graph_to_sentence(Cluster)
    
    img = ET.parse(os.path.join(app_directory, f'image_data/{image_id}')).getroot()
    for cap in img.iter('caption'):
        print("caption : ",cap.text)
    print("result : ", sentence)
    return sentence