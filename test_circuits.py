#import pytest
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
    correct_qubit,
    calculate_simple_parity_bits,
    calculate_parity,
    summarise_logical_counts,
    process_FT_results
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
            _ , count_invalid, _  = count_valid_output_strings(counts, codewords, 3)
            error_rate = count_invalid / SHOTS
            assert error_rate == 0.0

def test_error_correction_logical_one():
    """Checks that every X error gets corrected by error correction with and without MCT gates with logical one"""
    for mct in [True, False]:
        for index in range(7):
            qubit = SteaneCodeLogicalQubit(1, parity_check_matrix, 
                                            codewords, extend_ancilla = True)
            qubit.set_up_logical_zero(logical_one = True)
            qubit.force_X_error(index)   
            #force X error for testing
            qubit.set_up_ancilla()
            qubit.correct_errors(0, mct)
            qubit.logical_gate_X()
            qubit.logical_measure_data()
            qubit.logical_measure_ancilla()
            qt = transpile(qubit, basis_gates = BASIS_GATE_SET)
            result = execute(qt, SIMULATOR, shots = SHOTS).result()
            counts = result.get_counts(qt)
            _ , count_invalid, _  = count_valid_output_strings(counts, codewords, 3)
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
    _ , count_invalid, _  = count_valid_output_strings(corrected_counts, codewords, 2)
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
    """Checks that the bitwise function helper function correctly calculates the bitwise AND of two string"""
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

    count_valid, count_invalid, count_outside_codeword = count_valid_output_strings(counts, codewords, 2)
    assert count_valid == 3  #calculated from example above
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

def test_count_valid_output_strings_simple_zero():
    """Check that each logical zero codeword is identified as valid with simple software decoding"""
    counts =    {'0000000': 12, 
                 '0011110': 12, 
                 '0101101': 9, 
                 '0110011': 12, 
                 '1001011': 8, 
                 '1010101': 17, 
                 '1100110': 16, 
                 '1111000': 14
                 }
    count_valid , count_invalid, _ = count_valid_output_strings(counts, ['0'], 
                                                    simple = True
                                                    )
    assert count_valid == 100  #calculated from example given
    assert count_invalid == 0  #calculated from example given

def test_count_valid_output_strings_simple_one():
    """Check that each logical one codeword is identified as valid with simple software decoding"""
    counts =    {'0011001': 17, 
                 '0101010': 17, 
                 '0110100': 9, 
                 '1001100': 12, 
                 '1010010': 9, 
                 '1100001': 13, 
                 '0000111': 11, 
                 '1111111': 12
                 }
    count_valid , count_invalid, _ = count_valid_output_strings(counts, ['1'], 
                                                    simple = True
                                                    )
    assert count_valid == 100  #calculated from example given
    assert count_invalid == 0  #calculated from example given

def test_calculate_simple_parity_bits():
    """Checks the function to produce the bits for the simple parity checking."""
    simple_parity_bits = calculate_simple_parity_bits()
    assert simple_parity_bits == [2, 4, 5]

def test_count_valid_output_strings_simple_zero_random_codewords():
    """Check that validity for random codewords with a bit flip in one place is correctly calculated with simple software decoding"""
    counts =    {'0000001': 16, #flip 0th bit - valid as no impact
                 '0011100': 18, #flip 1st bit - valid as no impact
                 '0101001': 10, #flip 2nd bit - invalid
                 '0001000': 12, #flip 3rd bit - valid as no impact
                 '0010000': 8,  #flip 4th bit - invalid
                 '0100000': 13, #flip 5th bit - invalid
                 '1000000': 11  #flip 6th bit - valid as no impact
                 }
    count_valid , count_invalid, _ = count_valid_output_strings(counts, ['0'], 
                                                    simple = True
                                                    )
    assert count_valid == 16 + 18 + 12 + 11  #calculated from example above
    assert count_invalid == 10 + 8 + 13  #calculated from example above

def test_calculate_parity_even():
    """Checks the parity is properly calculated for an even parity bit string"""
    bit_string = '011'
    parity = calculate_parity(bit_string)
    assert parity == 0

def test_calculate_parity_odd():
    """Checks the parity is properly calculated for an odd parity bit string"""
    bit_string = '0110111'
    parity = calculate_parity(bit_string)
    assert parity == 1

def test_summarise_logical_counts():
    """Checks the summarisation of strings on some manufactured data"""

    corrected_counts = {'010 000 0011100 100 000 0011101': 1,  
                        # 0 0 first string in logical, second with indetectable error
                        '010 000 1010101 101 011 0000111': 2,  
                        # 0 1 first string in logical, second in logical zero
                        '010 000 0000001 010 010 0101010': 4, 
                        # 0 1 first string in logical zero with indetectable error, second in logical one
                        '010 000 1000000 101 000 1000000': 8,  
                        # 0 0 first and second string in logical zero with indetectable error
                        '010 000 0100000 110 000 1000000': 16, 
                        # 1 0 first string in logical zero with detectable error, second in logical zero with detectable error
                        '010 000 0000111 101 010 0000111': 3,  
                        # 1 1 first and second string in logical one
                        }
    
    expected_result = {'00': 9, '01': 6, '02': 0, '10': 16, '11': 3, '12': 0, '20': 0, '21': 0, '22': 0}

    new_counts = summarise_logical_counts(corrected_counts, 
                                              logical_zero_strings = ['0'], 
                                              logical_one_strings = ['1'],
                                              data1_location = 2, 
                                              data2_location = 5,
                                              simple = True
                                              )
    assert new_counts == expected_result

def test_process_FT_results_B():
    """Checks the processing of FT results for scheme B"""
    
    input = {'0000000 0000000 0000000 0000000': 1,  #valid string - accepted
             '0011110 0101101 0110011 1001011': 2,  #valid string - accepted
             '0011111 0101101 0110011 1001011': 4,  #invalid first string - rejected
             '0011110 0001101 0110011 1001011': 8,  #invalid second string - rejected
             '0011110 0101101 1111111 1001011': 16, #invalid third string - rejected
             '0011110 0101101 0000000 1001111': 32, #invalid data - invalid
            }
    error, rej, acc, valid, invalid = process_FT_results(input, codewords,
                                                        data_start = 3, 
                                                        data_meas_qubits = 1,
                                                        data_meas_repeats = 3, 
                                                        data_meas_strings = codewords
                                                        )
    calc_error = invalid / acc
    assert valid == 3       #valid results
    assert invalid == 32    #invalid results
    assert acc == 35        #accepted for processing
    assert rej == 28        #rejected before processing
    np.testing.assert_almost_equal(calc_error, error, decimal = 7, verbose = True)

def test_process_FT_results_C():
    """Checks the processing of FT results for scheme C"""
    
    input = {'0 0 0 0000000': 1,  #valid string - valid
             '1 0 0 0000001': 2,  #invalid first string - rejected,  
             '0 1 0 0011110': 4,  #invalid second string - rejected, 
             '0 0 1 1000000': 8,  #invalid third string - rejected, 
             '1 0 1 0000000': 16,  #invalid two strings - rejected, 
             '1 1 1 0000000': 31,  #invalid three strings - rejected, 
             '0 0 0 0000001': 32,  #invalid data string - invalid
             '0 0 0 1111111': 33,  #invalid data string - invalid
            }
    error, rej, acc, valid, invalid = process_FT_results(input, codewords, 
                                                          data_start = 3, 
                                                          data_meas_qubits = 1,
                                                          data_meas_repeats = 3, 
                                                          data_meas_strings = ['0'],
                                                          )
    calc_error = invalid / acc
    assert valid == 1       #valid results
    assert invalid == 65    #invalid results
    assert acc == 66        #accepted for processing
    assert rej == 61        #rejected before processing
    np.testing.assert_almost_equal(calc_error, error, decimal = 7, verbose = True)                                                           
                                                          
def test_process_FT_results_D():
    """Checks the processing of FT results for scheme D"""
    
    input = {'0000000 0000000 0000000 0000000': 1,  #valid string - accepted
             '0011110 0101101 0110011 1001011': 2,  #valid string - accepted
             '0011111 0101101 0110011 1001011': 4,  #invalid first string - rejected
             '0011110 0001101 0110011 1001011': 8,  #invalid second string - rejected
             '0011110 0101101 1111111 1001011': 16, #invalid third string - rejected
             '0011110 0101101 0000000 1001111': 32, #invalid data - invalid
            }
    error, rej, acc, valid, invalid = process_FT_results(input, codewords,
                                                        data_start = 3, 
                                                        data_meas_qubits = 1,
                                                        data_meas_repeats = 3, 
                                                        data_meas_strings = codewords
                                                        )
    calc_error = invalid / acc
    assert valid == 3       #valid results
    assert invalid == 32    #invalid results
    assert acc == 35        #accepted for processing
    assert rej == 28        #rejected before processing
    np.testing.assert_almost_equal(calc_error, error, decimal = 7, verbose = True)

def test_process_FT_results_C_anc():
    """Checks the processing of FT results for scheme C with FT ancillas"""
    
    input = {'0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0011110': 1,
             #valid data string
             '0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 1 0 0 0011110': 3, 
             #invalid first string - rejected,  
             '0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 1 0 0000001': 5, 
             #invalid second string - rejected,
             '0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 1 0000000': 7, 
             #invalid third string - rejected,
             '0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 1 0 1 0000000': 11, 
            # two invalid strings - rejected
             '0001 0001 0001 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0000001': 13,
            #correctable error in zeroth qubit - valid
             '0000 0000 0000 0001 0001 0001 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0000010': 17,
            # correctable error in first qubit - valid
             '0001 0001 0001 0001 0001 0001 0001 0001 0001 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0111000': 19,
            # correctable error in final qubit - valid
             '0001 0000 0001 0001 0001 0001 0001 0001 0001 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0111000': 23,
            #ancilla not the same - reject
             '0001 0001 0001 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0 0 0000011': 29,
            #error in zeroth qubit - invalid after correction
            }
    error, rej, acc, valid, invalid = process_FT_results(input, codewords,
                                                         anc_zero = '0000',
                                                         anc_one = '0001',
                                                         data_meas_start = 18, 
                                                         data_start = 21,
                                                         ancilla_qubits = 3, 
                                                         ancilla_meas_repeats = 3,
                                                         data_meas_qubits = 1, 
                                                         data_meas_repeats = 3,
                                                         )
    calc_error = invalid / acc
    assert valid == 50               #valid results
    assert invalid == 29             #invalid results
    assert acc == valid + invalid    #accepted for processing
    assert rej == 49                 #rejected before processing
    np.testing.assert_almost_equal(calc_error, error, decimal = 7, verbose = True)   