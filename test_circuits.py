import pytest
from pytest import raises
from circuits import SteaneCodeLogicalQubit
from qiskit import execute, Aer
from qiskit.compiler import transpile
import numpy as np

from helper_functions import (
    flip_code_words,
    string_reverse,
    strings_AND_bitwise,
    string_ancilla_mask,
    correct_qubit,
    flip_code_words,
    count_valid_output_strings,
    mean_of_list,
    calculate_standard_error, 
    correct_qubit 
    )

SINGLE_GATE_SET = ['id', 'ry', 'rx']
TWO_GATE_SET = ['rxx']
BASIS_GATE_SET = SINGLE_GATE_SET + TWO_GATE_SET
TEST_X_QUBIT = 4
DATA_QUBITS = 7
SHOTS = 100     #Number of shots to run    
SPACE = ' '
SIMULATOR = Aer.get_backend('qasm_simulator')

parity_check_matrix = ['0001111',
                       '0110011',
                       '1010101'
                      ]

codewords = ['0000000',
             '1010101',
             '0110011',
             '1100110',
             '0001111',
             '1011010',
             '0111100',
             '1101001'
            ]

def test_error_correction():
    """Checks that every X error gets corrected by error correction with and without MCT gates"""
    for mct in [True, False]:
        for index in range(7):
            qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, 
                                            codewords, extend_ancilla = True)
            qubit.set_up_logical_zero()
            qubit.force_X_error(index)   
            #force X error for testing
            qubit.set_up_ancilla()
            qubit.correct_errors(0, mct)
            qubit.logical_measure_data()
            qubit.logical_measure_ancilla()
            qt = transpile(qubit, basis_gates = BASIS_GATE_SET)
            result = execute(qt, SIMULATOR, shots = SHOTS).result()
            counts = result.get_counts(qt)
            count_valid, count_invalid = count_valid_output_strings(counts, codewords, 3)
            error_rate = count_invalid / SHOTS
            assert error_rate == 0.0

def test_software_error_correction():
    """Checks that every X error gets corrected by software"""
for index in range(7):
    qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, codewords)
    qubit.set_up_logical_zero()
    qubit.force_X_error(index)   #force X error for testing
    qubit.set_up_ancilla()
    qubit.logical_measure_data()
    qubit.logical_measure_ancilla()
    result = execute(qubit, SIMULATOR, shots = SHOTS).result()
    counts = result.get_counts(qubit)
    corrected_counts = {}
    for key, values in counts.items():
        #split out key
        data = key.split()[2]
        x_ancilla = key.split()[0]
        z_ancilla = key.split()[1]
        data = key.split()[2]
        corrected_data = correct_qubit(data, x_ancilla, DATA_QUBITS)
        corrected_key = x_ancilla + SPACE + z_ancilla + SPACE + corrected_data
        value_found = corrected_counts.get(corrected_key)
        if value_found:
            corrected_counts[corrected_key] = value_found + values
        else:
            corrected_counts.update({corrected_key: values})   
    count_valid, count_invalid = count_valid_output_strings(corrected_counts, codewords, 2)
    error_rate = count_invalid / SHOTS
    assert error_rate == 0.0

def test_no_error_correction_with_two_logical_qubits():
    """Checks that an error is thrown when a circuit is set up for extra ancilla for two logical qubits"""
    with raises(ValueError, match = "Can't set up extra ancilla with two logical qubits due to memory size restrictions"):
        SteaneCodeLogicalQubit(2, parity_check_matrix, codewords, extend_ancilla = True)

def test_physical_qubit_reference_in_range():
    """Checks that an error is thrown when indexing a physical qubit outside the valid range"""
    qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, codewords, False)
    qubit.set_up_logical_zero(0)
    with raises(ValueError, match = 'Qubit index must be in range of data qubits'):
        qubit.force_X_error(7,0)

def test_string_reverse():
    """Checks that the reverse string helper function is reversing correctly"""
    reversed_string = string_reverse('0001010')
    assert reversed_string == '0101000'

def test_strings_and_bitwise():
    """Checks that the bitwise function helper function correctly calcules the bitwise AND of two string"""
    bitwise_string = strings_AND_bitwise('0101010', '0001111')
    assert bitwise_string == '0100101'

def test_def_string_ancilla_mask():
    """Checks that the ancilla mask creation helper function is working correctly"""
    result = string_ancilla_mask(2, 4)
    assert result == '0010'

def test_correct_qubit():
    """Checks that the data qubit correction helper function is working correctly"""
    result = correct_qubit('0011100', '010', 7)
    assert result == '0011110'

def test_flipped_codewords():
    """Checks that the helper function to bit flip codewords module is working correctly"""

    flip = ['1111111',
            '0101010',
            '1001100',
            '0011001',
            '1110000',
            '0100101',
            '1000011',
            '0010110'
            ]
    
    result = flip_code_words(codewords)
    assert result == flip

def test_count_valid_output_strings():
    """Checks that the helper function to count valid output strings agrees to a preworked example"""
    counts = {
        '111 000 1000000': 1, # invalid
        '000 000 0101101': 1, # valid
        '000 000 1001011': 2, # valid
        '010 000 0100000': 1, # valid
    }

    count_valid, count_invalid = count_valid_output_strings(counts, codewords, 2)
    assert count_valid == 3  #calcuLated from example above
    assert count_invalid == 2

def test_mean():
    """Checks that the mean of a list is correctly calculated"""
    test_list = [1, 2, 3, 4, 5]
    mean = mean_of_list(test_list)
    np.testing.assert_almost_equal(mean, 3, decimal = 7, verbose = True)

def test_standard_error():
    """Checks that the mean of a list is correctly calculated"""
    test_list = [1, 2, 3, 4, 5]
    standard_deviation, standard_error = calculate_standard_error(test_list)
    np.testing.assert_almost_equal(standard_deviation, 1.58113883, decimal = 7, verbose = True)
    np.testing.assert_almost_equal(standard_error, 0.70710678, decimal = 7, verbose = True)