import pytest
from pytest import raises
from circuits import SteaneCodeLogicalQubit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer

TEST_X_QUBIT = 4
SHOTS = 100     #Number of shots to run    
SIMULATOR = Aer.get_backend('qasm_simulator')
parity_check_matrix =  [[0,0,0,1,1,1,1],
                        [0,1,1,0,0,1,1],
                        [1,0,1,0,1,0,1]]

def test_parity_validation():
    """test that a random errors gets fixed"""
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

def test_no_error_correction_with_two_logical_qubits():
    """check that an error is thrown if try error correction with two logical qubits"""
    with raises(ValueError, match = "Can't correct errors with two logical qubits due to memory size restrictions"):
        SteaneCodeLogicalQubit(2, parity_check_matrix, True)

def test_logical_qubit_reference_in_range():
    """check that an error is thrown if try and set up a logical zero with an index greater than 1"""
    qubit = SteaneCodeLogicalQubit(2, parity_check_matrix, False)
    with raises(ValueError, match = "The qubit to be processed must be indexed as 0 or 1 at present"):
        qubit.set_up_logical_zero(2)

def test_physical_qubit_reference_in_range():
    """check that an error is thrown if try and index a physical qubit outside the valid range"""
    qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, False)
    qubit.set_up_logical_zero(0)
    with raises(ValueError, match = "Qubit index must be in range of data qubits"):
        qubit.force_X_error(7,0)

    


    

       