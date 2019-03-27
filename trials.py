import ptg
import csv
import grounding_orig as grounding

domain = "domain_miconic.pddl"

with open('trials_fullinit.csv', 'w', newline='') as csvfile:
    fieldnames = ['Name', 'Diameter', 'Radius']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for p in range(2, 101):
        f_name = "f%dp1.pddl" % p
        problem = ptg.parse(domain, "./floors_fullinit/%s" % f_name)
        task = ptg.ground(problem)
        diameter, radius = ptg.build_graph_related(task, 
                                                   static=True, draw=False)
        writer.writerow({'Name': f_name, 'Diameter': diameter, 'Radius': radius})

