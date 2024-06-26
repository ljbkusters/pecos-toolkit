# pecos-toolkit



## Description
This project is a toolkit developed for PECOS based quantum circuit simulations of quantum error correction codes (QECCs). Currently, this project implements:

+ A Steane code simulator up to circuit noise.
+ Fault tolerant flag based error detection circuits.
+ A fault tolerant Look-Up-Table (LUT) decoder
+ A fault tolerant sequential LUT (SeqLUT) decoder.
+ A fault tolerant fully connected neural network decoder.
+ A fault tolerant recurrent neural network decoder.

The toolkit implements a few changes to the standard pecos QuantumCircuit,
extending its features. It also offers a highly customizable error generator
and a circuit runner with extended features. The repository aims to be an
object oriented implementation which is in line with PECOS.

## Visuals
The stean code visualized as a graph
![Steane code graph](figures/steane-code-graph.jpg)

Flag based steane code readout circuit example for plaquette $X_{1234}$

![Example flag based steane readout circuit](figures/flag1-steane-meas-x.jpg)

Steane code readout scheme for all plaquettes.
![Steane readout scheme for all plaquettes](figures/readout-schedule.jpg)

Fault tolerant RNN decoder.
![RNN Decoder architecture](figures/control-scheme.jpg)

## Dependencies
This package depends on the PECOS version provided by Sascha Heußen. Currently
there is no public repository for this version.

## Installation
To install this package follow these steps:

+ Download or clone this repository
+ Open the project root directory
+ (Make sure to activate your virtual environment where PECOS is installed if
  you are using one)
+ run `pip install .` for a regular install or `pip install . -e` in dev mode.
  The second command will ensure that you can keep developing the package
  without having to reinstall it.

## Getting Started
For questions on how to use this toolkit, please contact me.

## Authors and acknowledgment
+ Luc Kusters
+ Lukas Bödeker and Markus Müller: Helped me with many theoretical questions
+ CR Anderson: Creator of QuantumPECOS

## License
This project is licensed under the gnu general public license v3

## Project status
This project is no longer under development and may be considered archived.
