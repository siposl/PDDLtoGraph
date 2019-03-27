# PDDLtoGraph

PDDLtoGraph is a simple program for visualising PDDL files as 
relatedness and causal graphs, written in python. 
It also determines the diameter and the radius of the graph.

## Requirements
Make sure the following program and packages are installed:

+ python3
+ pip3
+ [pyperplan](https://bitbucket.org/malte/pyperplan/src)
+ [networkx](https://networkx.github.io/)
+ [pygraphviz](https://pygraphviz.github.io/)

````
sudo apt install python3
sudo apt install python3-pip
pip3 install networkx
pip3 install pygraphviz
````

## Usage
The programm can be started by running **ptg.py**. It has 
requires two arguments a PDDL domain file and a PDDL problem description.
````
python3 DOMAIN PROBLEM
````

Optional arguments can also be invoked:

+ ````-h, --help````:  shows the help message
+ ````-l, --loglevel````:  pyperplan log level
  + available levels are: ````{debug,info,warning,error}```` 
+ ````-g, --graphtype````:  choose between the graph types
  + available types are: ````{relatedness,causal,rel_simple}```` 
+ ````--grounding````:  select wich grounding method is chosen
  + ````original````: pyperplans original grounding
  + ````new````: slightly modified version, without pruning
+ ````-d, --diameter````:  toggle the drawing of diameter length path
  + available options are: ````{true, false}```` 



## Examples
#### Relatedness Graph
![relatedness](./img/img_relatedness.png)
#### Simplified Relatedness Graph
![relatedness](./img/img_rel_simple.png)
#### Causal Graph
![relatedness](./img/img_causal.png)
