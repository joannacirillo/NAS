import json
import sys

if __name__=="__main__":
    if(len(sys.argv)!=2):
        print("Invalid arguments. Please run as:")
        print("python3 scriptGNS.py <json-config-file-name>")
        sys.exit()

    with open(sys.argv[1]) as file: # ouverture du json qui décrit le réseau
        f = json.load(file)
        args = f["routers"]
        nb_routeurs = len(args)

    for i in range(nb_routeurs):    # pour chaque routeur

        name = (args[i])["name"] + "_configs_i" + str(i+1) + "_private-config.cfg"
        with open(name, "w") as config: # ouverture du script à écrire
            config.write("# " + (args[i])["name"] + "\n")
            config.write("configure terminal\n")

            # Configuration OSPF
            if "ospf" in (args[i])["protocols"]:
                config.write("router ospf " + (args[i])["process_id"] +"\n")
                for j in range(len((args[i])["interfaces"])):
                    intj = ((args[i])["interfaces"])[j]
                    # Ne pas mettre les réseaux des vrf dans le routage ospf classique
                    if "PE" in (args[i])["name"] :
                        if intj["vrf"]=="" :
                            config.write("  network "+intj["subnet_address"]+" "+intj["inverted_mask"]+" area "+(args[i])["area"]+"\n")
                    else :
                        config.write("  network "+intj["subnet_address"]+" "+intj["inverted_mask"]+" area "+(args[i])["area"]+"\n")

                if "P" in (args[i])["name"]:
                    config.write("router ospf router-id loopback 0\n")
                else :
                    config.write("router-id " + (args[i])["router_id"] +"\n\n")

            # Configuration mpls globale au routeur
            if "mpls" in (args[i])["protocols"]:
                config.write("ip cef\n")
                config.write("mpls label range " + (args[i])["label_range"] + "\n\n")
                config.write("mpls ldp router-id loopback 0\n")
  
            if "PE" in (args[i])["name"]:

                # Configuration des vrf
                for j in range(len((args[i])["vrf"])):
                    vrfj = ((args[i])["vrf"])[j]
                    config.write("ip vrf "+ vrfj["vrf_name"]+"\n")
                    if vrfj["rd"]!= "" : 
                            config.write("  rd "+(args[i])["as_bgp"]+":"+vrfj["rd"]+"\n")
                    for export in vrfj["export"] :
                        # Permettre aux autres routeurs de router avec cette vrf
                        config.write("  route-target export "+(args[i])["as_bgp"]+":"+export+"\n")
                    for import_id in vrfj["import"] :
                        # Permettre au routeur de router avec cette vrf
                        config.write("  route-target import "+(args[i])["as_bgp"]+":"+import_id+"\n")
                    config.write("  exit\n\n")

                    # Configuration des sessions ospf des vrf
                    config.write("  router ospf "+((args[i])["process_id"])+str(j+1)+" vrf "+vrfj["vrf_name"]+"\n")
                    config.write("  redistribute bgp "+(args[i])["as_bgp"]+" subnets \n")
                    for n in range(len((args[i])["interfaces"])):
                        intn = ((args[i])["interfaces"])[n]
                        if intn["vrf"]==str(vrfj["vrf_name"]) :
                            config.write("  network "+intn["subnet_address"]+" "+intn["inverted_mask"]+" area "+(args[i])["area"]+"\n\n")

                    # Configuration d'une session bgp
                    config.write("  router bgp "+(args[i])["as_bgp"]+"\n")
                    for neighbor in (args[i])["neighbors"]:
                        config.write("      neighbor "+neighbor+" remote-as "+(args[i])["as_bgp"]+"\n")
                        config.write("      neighbor "+neighbor+" update-source loopback 0\n\n")
                        
                        config.write("  address-family vpnv4 \n")
                        config.write("      neighbor "+neighbor+" activate\n")
                        config.write("      neighbor "+neighbor+" send-community extended\n")
                        config.write("      neighbor "+neighbor+" next-hop-self\n")
                        config.write("      exit-address-family\n\n")
                    
                    config.write("  address-family ipv4 vrf "+vrfj["vrf_name"] +"\n")
                    config.write("      redistribute ospf "+((args[i])["process_id"])+str(j+1)+" vrf "+vrfj["vrf_name"] +"\n")
                    config.write("      no synchronization\n")
                    config.write("      exit-address-family\n\n")
                    config.write("  exit\n\n")

            if "P" in (args[i])["name"] :
                QoS = f["QoS"]
                for qos_class in (QoS)["classes"] :
                    # Définition des classes
                    config.write("class-map "+qos_class["name"]+"\n")
                    config.write("  match access-group "+qos_class["access-list"]+"\n")
                    config.write("  exit\n\n")
                    config.write("access-list "+qos_class["access-list"]+" permit "+qos_class["name"]+" any any \n\n")

                    # Définition des politiques
                    for policy in QoS["policies"]:

                        if policy["policy_map"]!="IN":
                            
                            for current_pol_classes in policy["classes"]:
                                try:
                                    if current_pol_classes[qos_class["name"]] :
                                        current_class = current_pol_classes[qos_class["name"]]
                                        config.write("policy-map "+policy["policy_map"]+"\n")
                                        config.write("  class "+qos_class["name"]+"\n")
                                        # Configuration des exigences à respecter
                                        try:
                                            if current_class["bandwidth"]:
                                                config.write("      bandwidth percent "+current_class["bandwidth"]+"\n")
                                                config.write("      exit\n")
                                        except KeyError:
                                            pass
                                        config.write("  exit\n\n")
                                except KeyError:
                                    pass

                        elif "PE" in (args[i])["name"] :
                            # Configurer le dscp de la classe
                            config.write("policy-map "+policy["policy_map"]+"\n")
                            config.write("  class "+qos_class["name"]+"\n")
                            config.write("      set ip dscp "+qos_class["dscp"]+"\n")
                            config.write("      exit\n")
                            config.write("  exit\n\n")
                    
                config.write("class-map BESTEFFORT \n")
                config.write("  match ip dscp default \n")
                config.write("  exit\n\n")        

            # Configuration des interfaces du routeur
            for j in range(len((args[i])["interfaces"])):   # pour chaque interface du routeur
                intj = (((args[i])["interfaces"])[j])   # intj = tableau qui contient le nom de l'interface, son adresse, etc.
                config.write("interface " + intj["interface"]+"\n")
                config.write("  ip address " + intj["address"] + " " + intj["prefix_length"] + "\n")
                config.write("  no shutdown\n")

                # Implémentation d'mpls sur les interfaces à l'intérieur du réseau du provider
                if "mpls" in intj["protocols"]:
                    config.write("  mpls ip \n")
                    config.write("  mpls mtu override "+intj["mpls_MTU"]+"\n")   
                # Lien entre les vrf et les adresses ip correspondantes.
                if "PE" in (args[i])["name"] :   
                    try :
                        if intj["ext"]=="true":
                            # Appliquer la politique d'entrée 
                            config.write("  service-policy input IN\n")
                    except KeyError:
                        pass

                    if intj["vrf"]!= "" :
                        config.write("  ip vrf forwarding "+intj["vrf"]+"\n")
                        config.write("  ip address " + intj["address"] + " " + intj["prefix_length"] + "\n")

                if "P" in (args[i])["name"] and intj["interface"]!="Loopback0":
                    QoS = f["QoS"]
                    for policy in QoS["policies"]:
                        if policy["policy_map"]!="IN":
                            config.write("  service-policy output "+policy["policy_map"]+"\n")

                config.write("  exit\n\n")

            config.write("end\n\n")