import networkx as nx
import xml.etree.ElementTree as ET
import os
import csv

def degree_sortant(G):
    return nx.degree_centrality(G.reverse())

def degree(G):
    nodes = nx.degree_centrality(G)
    for k,v in degree_sortant(G).items():
        nodes[k] += v
    return nodes

Centrality = {
              "betweenness":nx.betweenness_centrality,
              "degree":degree,
              "degree_entrant":nx.degree_centrality,
              "degree_sortant":degree_sortant,
              "closeness":nx.closeness_centrality,
              "eigenvector":nx.eigenvector_centrality_numpy
              }

Max = 2000
Tout_Objs = None
Tout_Preds = None
Tout_Attr = None

def treat_xml_obj(x:ET.Element,attrs:list) -> dict:
    r = {}
    attributes = []
    for sub in x.iter():
        if sub.tag == 'object' or sub.tag == 'attributes':
            continue
        if sub.tag == 'attribute':
            for a in attrs:
                if a['Name'] == x.findtext('./name'):
                    attr = a['attributes']
                    break
            
            if not attrs or sub.text in attr:
                attributes.append(sub.text)
        else:
            r[sub.tag] = sub.text

    r['attributes'] = attributes
    return r

def CreateGraph(image_id:str,nb_obj = 0,nb_rel = 0,nb_attr = 0):
    """
    G c'est le scene graph de l'image dont l'id VG est image_id avec ces noeuds les object id et 
    ```
    object_name = lambda G,object_id: G.nodes[object_id]['name']
    attributes = lambda G,object_id: G.nodes[object_id]['attributes']
    predicate = lambda G,subject_id,object_id: G.edges[(subject_id,object_id)]['predicate']
    ```

    ---

    nb_obj: On prend en consideration que les nb_obj objet les plus communs dans la datatset
    nb_rel: On prend en consideration que les nb_rel predicat les plus communs dans la datatset
    nb_attr: On prend en consideration que les nb_attr attribut les plus communs dans la datatset
    """
    objs = []
    preds = []
    attrs = []
    global Tout_Objs
    global Tout_Preds
    global Tout_Attr
    global Max

    if nb_obj>Max or nb_rel>Max:
        Max = max(nb_obj,nb_rel)
        Tout_Objs = None
        Tout_Preds = None

    if nb_obj and not Tout_Objs:
        obj_csv = csv.reader(open('./params/object_params.csv'))
        Tout_Objs = [obj[0] for obj in obj_csv][1:Max+1]

    if Tout_Objs:
        objs = Tout_Objs[:int(nb_obj)+1]

    if nb_rel and not Tout_Preds:
        pred_csv = csv.reader(open('./params/predicate_params.csv'))
        Tout_Preds = [pred[0] for pred in pred_csv][1:Max+1]

    if Tout_Preds:
        preds = Tout_Preds[:int(nb_rel)+1]

    def parse_int(i):
            try:
                return int(i)
            except:
                return 0

    def treat_attr_dict(attr):
        attr['Nb1'] = parse_int(attr['Nb1'])
        attr['Nb2'] = parse_int(attr['Nb2'])
        return attr

    if nb_attr and not Tout_Attr:
        attr_csv = csv.DictReader(open('./params/attributes.csv'))
        Tout_Attr = [treat_attr_dict(attr) for attr in attr_csv]


    if Tout_Attr:
        print()
        for attr in Tout_Attr:      
            attributes = []
            if attr['Nb1'] >= nb_attr:
                attributes.append(attr['Attribute 1'])
            if attr['Nb2'] >= nb_attr:
                attributes.append(attr['Attribute 2'])

            attrs.append({'Name':attr['Name'],'attributes':attributes})
    
    
    img = ET.parse(f'./image_data/{image_id}').getroot()

    G = nx.DiGraph(id = image_id.split('.')[0])

    # s'il est nécéssaire on rajouter {'xml_obj':x}
    G.add_nodes_from([(x.findtext('./object_id'),treat_xml_obj(x,attrs)) for x in img.findall('./objects/object') if not nb_obj or x.findtext('./name') in objs])

    G.add_edges_from([
                        (
                            x.findtext('./subject'),x.findtext('./object'),
                            {
                                'predicate':x.findtext('./predicate'),
                                'weight':preds.index(x.findtext('./predicate')) if nb_rel else 0
                            }
                        ) 
                      for x in img.findall('./relationships/relationship')

                      if not nb_rel or x.findtext('./predicate') in preds and x.findtext('./subject') in G and x.findtext('./object') in G
                    ])

    return G


# J'ai l'a mis dans une fonction dans le cas on veut une autre méthode de choisir le big dans le cas d'exception 
def select_big(G,l):
    """
    G: Le scene Graph
    l: liste des tuple (node,score)

    #### Retur result
    x un élément de l qui a été choisi comme le big 
    """
    # Quand cette fonction est appelé l'alocation de Tout_Objs est déjà faites
    # et on n'a pas besoin de élargir Tout_Objs parce que tous les noms des neouds de G y appartiennent déjà

    #obj_csv = csv.reader(open('./PFE/params/object_params.csv'))
    #Tout_Objs = [obj[0] for obj in obj_csv][1:]
        
    min = None
    for node in G.nodes(data = True):
        if min == None :
            name = node[1]['name']#['xml_obj'].findtext("./name")
            if name not in ['grass','floor','ground']:
                id = node[0]
                min = Tout_Objs.index(name)
        else :
            name = node[1]['name']#['xml_obj'].findtext("./name")
            if name not in ['grass','floor','ground']:
                i = Tout_Objs.index(name)
                if i < min :
                    id = node[0]
                    min = i
    for x in l:
        if x[0] == id:
            break
    return x

def select_biggest_area(G,l):
    max = None
    for node in G.nodes(data = True):
        if max == None and node[1]['name'] not in ['grass','floor','ground'] :
            max = int(node[1]['h']) * int(node[1]['w'])
            id = node[0]
        else :
            s = int(node[1]['h']) * int(node[1]['w'])
            if s > max and node[1]['name'] not in ['grass','floor','ground']:
                max = s
                id = node[0]
    for x in l:
        if x[0] == id:
            break
    return x


def centrality_cluster(G:nx.Graph,seuil:float,centrality):
    if not G:
        return nx.DiGraph()
    
    nodes = Centrality[centrality](G)

    l = list(nodes.items())
    print(l)
    big = max(l,key=lambda  x: x[1])

    if big[1] == 0:
        big = select_biggest_area(G,l)

    ds = set()
    ds.add(big[0])

    neis = set()
    neis = neis.union(ds)

    while True:
        used = set()
        for nei in neis:
            neis = neis.union([node for node in G.adj[nei] if nodes[node] >= seuil])
            neis = neis.union([node for node in G.predecessors(nei) if nodes[node] >= seuil])
            used.add(nei)
        
        if not neis.difference(ds):
            break

        ds.update(neis)
        neis.difference_update(used)

    C = G.subgraph([node for node in ds])
    
    C.graph['Central_node'] = big[0]

    # Ajouter la centralité des noeuds comme un attribut dans les noeuds du cluster
    for node in C.nodes:
        C.nodes[node]['centrality_score'] = nodes[node]

    #C.graph['id'] = G.graph['id']
    return C

def FromGraphToXML(G:nx.Graph,seuil,method):
    if not G:
        print("empty Cluster")
        return
    image_id = G.graph['id']
    name = f'./{method}_cluster_{image_id}_{seuil}.xml'

    import os
    if os.path.exists(name):
        os.remove(name)

    clst = ET.Element("Cluster")

    elem = ET.Element("objects")
    elem.extend([G.nodes[x]['xml_obj'] for x in G.nodes])
    clst.append(elem)

    elem = ET.Element('relationships')

    def make_rel(x):
        object_id,subject_id = x

        rel = ET.Element('relationship')
        elem = ET.Element('object')
        elem.text = object_id
        rel.append(elem)
        
        elem = ET.Element('subject')
        elem.text = subject_id
        rel.append(elem)

        elem = ET.Element('predicate')
        elem.text = G.edges[x]['predicate']
        rel.append(elem)

        return rel

    elem.extend([make_rel(x) for x in G.edges])
    clst.append(elem)

    root = ET.ElementTree(clst)
    #ET.indent(root)

    with open(name,'x'):
        root.write(name,encoding="utf-8")
