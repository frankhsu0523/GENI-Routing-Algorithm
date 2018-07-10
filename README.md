Implementation and Evaluation of Offline Routing Algorithms in Software Defined-Netowrk on GENI
======================================================================================
Introduction...

## Table of Contents

- [Requirements](#requirements)
  - [GENI account](#GENI)
  - [Topology file](#topology-file)
  - [Path file](#path-file)
- [Getting Started](##getting-started)
  - [Create RSpec](#create-rspec)
  - [Creat network](#create-network)




##  Requirements
### GENI account
For using this program, you will need a GENI account first. In [GENI](http://www.geni.net/ "GENI"), following the official's directions to register the account. After registration, you need to either join or host a project so you could start to implement a experiment.

### Topology file
To create a SDN network on GENI, you need to create a topology file. You need to following the format in the example of the file. Once create the file, we could use this program to covert it into the rspec format which GENI could read.

### Path file
Path file is the output of the offline routing algorithm. The format of the path file should follow the example of the path file that the program could run it courrectly.

## Getting Started
### Create RSpec
First, we need to create the SDN on GENI. The content of the graph file describe the network's topology including link bandwidth and node capacity. Run the following code to convert the graph file into RSpec file.
```Bash
python create_rspec.py "graph_file (txt)"
```
### Create network
To create a SDN, we use [GENI Desktop](https://genidesktop.netlab.uky.edu/ "GENI Desktop") to create our network. After logging into [GENI Desktop](https://genidesktop.netlab.uky.edu/ "GENI Desktop"), create a slice for your experiment. Once you create your slice, you could import the RSpec file. 
![](http://github.com/frankhsu523/GENI-Routing-Algorithm/images/geni_desktop.png)




