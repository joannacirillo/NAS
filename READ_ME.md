# TP NAS

Quentin Vittoz, Israël Ibanez, Pénélope Roullot, Joanna Cirillo

Le script "scriptGNS.py" est un script (python) qui permet de générer un configuration de routeur pour GNS3 à partir d'un fichier de configuration en .json.
Pour le lancer : python3 scriptGNS.py <nom-du-fichier-de-configuration> 

Il génère :
    _ la configuration des adresses IP sur les interfaces
    _ un routage ospf entre les routeurs client et provider
    _ un routage bgp entre les provider edges
    _ un routage mpls entre les routeurs de coeur de réseau
    _ la configuration de VRFs
    _ la configuration de QoS

Le fichier json contient comme 1er élément du dictionnaire la liste des routeurs à configurer.

```
{
    "name" : <Nom-du-routeur>,
    "interfaces" :
        [
            {
                "interface":<nom-de-l-interface>,
                "address" : <adresse>,
                "subnet_address": <masque-de-sous-reseau>,
                "inverted_mask" : <masque-de-sous-reseau-inverse>,
                "prefix_length": <prefixe-en-decimal>,
                "protocols": <protocoles-implementes-sur-l-interface>,
                "mpls_MTU" : <mtu> ,
                "area": <aire-bgp>,
                "ext":<renseignee-a-"true"-si-l-interface-permet-de-sortir-du-reseau-provider> **,
                "vrf" : <nom-de-la-vrf-associee> **
            }
        ],
    "loopback" : <adresse-de-loopback> *,
    "protocols": <protocoles-a-implementer>,
    "area" :<aire-bgp>,
    "process_id": <id-process-ospf-principal>,
    "router_id": <id-du-routeur>,
    "label_range" : <plage-pour-labels-mpls> *,
    "as_bgp" : <numero-d-as-bgp> **,
    "vrf" : [
          {
            "vrf_name" : <nom-de-la-vrf>,
            "rd" : <route-distinguisher-pour-la-vrf>,
            "import" : [<liste-des-tags-a-importer>],
            "export" : [<liste-des-tags-a-importer>]          
          }
        ],
      "neighbors" : [<liste-des-voisins-bgp>]
}
```

( * ) Ces champs n'existent que sur les routeurs du réseau coeur
(**) Ces champs n'existent que sur les routeurs de bords du coeur de réseau

Le format de la configuration des routeurs oblige à renseigner spécifiquement les adresses de toutes les interfaces. Une amélioration possible serait d'implémenter un algorithme permettant de calculer des adresses uniques sur les sous-réseaux si aucune adresse n'est renseignée.

Le second élément du dictionnaire permet de renseigner les politiques de QoS.
```
"QoS" : {
    "classes" : [
      {
        "name" : <nom-de-la-classe>,
        "access-list" : <numero-de-l-accesslist-correspondant>,
        "dscp" : <dscp-de-la-classe>
      }
    ],
    "policies" : [
      { "policy_map" : <nom-de-la-policy-map>,
        "classes" : [
            {
                <nom-de-la-classe> : {
                  "bandwidth" : <pourcentage-de-bande-passante-a-allouer>
                }
            }
        ]
      }
    ]
  }
```
Pour chaque classe de trafique, on associe une accesslist (dont le numéro est partagé par tous les routeurs qui implémentent de la QoS) pour pouvoir définir des politiques à appliquer à cette classe. Les politiques à appliquer sont ensuite définies dans des policy-map qui sont ensuite appliquées à des interfaces. Chaque classe de trafic a également un dscp, qui correspond à sa priorité pour le réseau.

Nous avons dans notre implémentation deux classes de trafic, une pour le trafic TCP et une autre pour le trafic UDP. Nous avons donc une politique en entrée qui consiste à renseigner le champ DSCP des paquets entrant dans le coeur de réseau (appelée IN) et une autre qui applique une politique sur la bande passante dans les paquets à l'intérieur du réseau (appelée MARKED).

Une amélioration possible de notre script consisterait à pouvoir mettre des paramètres autres que la bande passante.
