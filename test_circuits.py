import pytest
from circuits import SteaneCodeLogicalQubit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer

TEST_X_QUBIT = 4
SHOTS = 100     #Number of shots to run    
SIMULATOR = Aer.get_backend('qasm_simulator')

def test_parity_validation():
    """test that a random errors get fixed"""
    parity_check_matrix =  [[0,0,0,1,1,1,1],
                            [0,1,1,0,0,1,1],
                            [1,0,1,0,1,0,1]]
    for test_X_qubit in range(6):
        qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, True)
        qubit.set_up_logical_zero(0)
        qubit.force_X_error(test_X_qubit,0)   #force X error for testing
        qubit.set_up_ancilla(0)
        qubit.decode(0)
        result = execute(qubit, SIMULATOR, shots=SHOTS).result()
        counts = result.get_counts(qubit)
        for key in counts.keys():
            assert(key[-7:]) == "0000000"
        #length = len(result.get_counts(qubit))
        #assert length == 1
    

       