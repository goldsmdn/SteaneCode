# SteaneCode
## MSc Steane Code project

For documentation of the SteaneCodeLogicalQubit class please see the automatically produced [documentation](https://goldsmdn.github.io/SteaneCode/).

Please see the [Pipecleaning repository](https://github.com/goldsmdn/Pipecleaning_test) for the initial work from which the baseline files were copied.

## List of workbooks
Workbook *Steane Code* is a good place to start.  It illustrates the main method calls.

The following additional workbooks are included:

### Basic tests
 - *Basic_single_qubit_errors.ipynb* : Compares simulation of parallel single-qubit gates to calculation.
 - *Basic_single_qubit_errors_transpilation.ipynb* : Compares simulation of parallel single-qubit gates to calculation for transpiled gates.
 - *Steane Code single-qubit error sensitivity* : Finds sensitivity of simulations to single-qubit errors.
 - *Basic_two_qubit_errors.ipynb* : Compares simulation of parallel two qubit gates to calculation.

### Calibration of noise model
 - *Egan_single_qubit_errors.ipynb* :  Compares simulation of randomised benchmarking of Clifford gates to Egan’s observations.  
 - *Egan_two_qubit_errors.ipynb* : Compare simulation of parallel XX gates to Egan’s experimental observations.  
 - *Bacon_Shor_1.ipynb* : Simulation of full Bacon Shor code 1.
 - *Bacon_Shor_1.ipynb* : Simulation of full Bacon Shor code 2.

### Steane code encoding
 - *Steane Code encoding* : Check how much noise is introduced by the encoding circuit.
 - *Steane Code encoding FTb* :  Test fault tolerance encoding using scheme B from Goto.
 - *Steane Code encoding FTc* :  Test fault tolerance encoding using scheme C from Goto.
 - *Steane Code encoding FTd* :  Test novel fault tolerance encoding scheme D.
 - *Steane Code FT encoding* : Plots performance of a single-qubit, non fault tolerant encoding and scheme B, C and D. 

 ### Steane code error correction
 - *Steane Code correction no noise* : Ensures that when there is no noise any errors introduced on the Steane code are corrected.
 - *Steane Code correction noise* : Assess the noise introduced by error correction.
 - *Steane Code error detection software decoding with noise* : Measures errors before and after error correction, with and without noise.  

 ### Steane code decoding
 - *Steane Code decoding with noise* : Assess noise introduced by each the measurement, encoding, detection and decoding stages.
 - *Steane Code decoding no noise* : Ensures that when there is no noise any errors introduced on the Steane code are corrected and are the results are decoded correctly. 

 ### Logical operations
 - *Steane Code logical operation* : Sets up a circuit to produce a logical Bell pair.
 - *Steane Code logical operation test software decoding with noise* : Test the decoding software by introducing errors and making sure these get corrected.
 - *Steane Code logical operation software decoding with noise and without transpilation* : Carries out a sensitivity analysis of the performance of a physical and logical Bell pair at different noise levels.

 ### Sundry circuits
 - *Count gates* : Counts gates in transpiled error correction circuits.