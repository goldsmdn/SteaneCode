#helper_functions.py

from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import (
    pauli_error, 
    depolarizing_error,
    thermal_relaxation_error
    )
from statistics import stdev
from math import sqrt
from datetime import datetime

SPACE = ' '

def string_reverse(input_string):
    """Reverses a string.

    Parameters
    ----------
    input_string : str
        Holds the string to be reversed
        
    Returns
    ----------
    reversed_string : str
        The reversed string  
            
    """
    
    reversed_string = input_string[::-1]

    return(reversed_string)

def find_parity(counts, data_qubits):
    """Finds the parity of the output bit string.

    Parameters
    ----------
    counts : dictionary
        Holds the observed output bit strings
    data_qubits : integer
        number of data qubits
        
    Returns
    ----------
    parity_count : dict
        A dictionary holding the partiy count for each observed output bit string.     
    """

    #initialise dictionary to hold counts
    parity_count = {str(i) : 0 for i in range(2)}
    for key, value in counts.items():
        #split out data part of key
        data = key.split()[1]
        parity = 0
        for i in range(data_qubits):
            bit = data[i]
            if bit == '1':
                #parity has changed
                if parity == 0:
                    parity = 1
                elif parity == 1:
                    parity = 0
                else:
                    raise Exception("Unexpected error calculating parity")
        old_count = parity_count[str(parity)]
        new_count = old_count + value
        parity_count[str(parity)] = new_count
    return(parity_count)

def count_valid_output_strings(counts, codewords, data_location = 0, 
                                post_selection = False, simple = False,
                                single = False, single_bit = 0):
    """Finds the number of valid and invalid output bit strings 
    in a given location in a dictionary representing
    the counts for each output bit string.  
    Various algorithms for determining validaty are supported,
    including post selection, where a bit is only valid if it is the codewords,
    simple decoding based on the parity of three bits and
    looking at a single bit only.

    Parameters
    ----------
    counts : dictionary
        holds the observed populations for each 
        combination of qubit
    codewords : list
        holds allowed codewords 
    data_location : int 
        location of the data string
    post_selection : bool
        if true then only strings in logical zero are invalid.
        Strings outside the codespace are counted separately.
    simple : bool
        looks only at the parity of bits with exactly two non-zero columns in the parity matrix
    single : bool
        look at single bit only
    single_bit : int
        single bit to validate against

    Returns
    -------
    count_valid : int
        Number of valid bit strings
    count_invalid : int
        Number of invalid bit strings
    count_outside_codeword : int
        Number of strings outside codespace.

    Notes
    -----
    This code was originally designed to handle the codewords 
    in a list of lists, but will also work fine
    with a list of strings.  

    """
    validate_integer(single_bit)
    if single:
        if len(codewords) != 1:
            raise ValueError('Only send a one bit codeword with calculation using a single bit')
        if simple:
            raise ValueError('Validity calculation not designed for both simple algorithm and single_bit')
        if post_selection:
            raise ValueError('Validity calculation not designed for both post_selection and single_bit')
    if simple:
        if post_selection:
            raise ValueError('Validity calculation not designed for both post_selection and simple')
        if len(codewords) != 1:
            raise ValueError('Only send a one bit codeword with simple calculation')
    count_valid = 0
    count_invalid = 0
    count_outside_codeword = 0
    for key, value in counts.items():
        #split out data part of key
        if data_location == 0:
            data = key
        else:
            data = key.split()[data_location]
        #need to reverse the data string showing the relevant qubits as 
        #the codewords and the data have a different format 
        reversed_data_string = string_reverse(data)
        valid, invalid, outside_codeword = compute_string_validity(value = value, codewords = codewords, 
                                                                reversed_data_string = reversed_data_string, 
                                                                post_selection = post_selection, 
                                                                simple = simple, 
                                                                single = single, 
                                                                single_bit = single_bit
                                                                )
        count_valid = count_valid + valid
        count_invalid = count_invalid + invalid
        count_outside_codeword = count_outside_codeword + outside_codeword
    return(count_valid, count_invalid, count_outside_codeword)

def compute_string_validity(value, codewords, reversed_data_string, post_selection = False, 
                            simple = False, single = False, single_bit = 0):
    """Finds the number of valid and invalid output bit strings 
    in a given location in a dictionary representing
    the counts for each output bit string.  
    Various algorithms for determining validaty are supported,
    including post selection, where a bit is only valid if it is the codewords,
    simple decoding based on the parity of three bits and
    looking at a single bit only.

    Parameters
    ----------
    value : int
        number of strings for this data string
    codewords : list
        holds allowed codewords 
    reversed_data_string : str
        string holding element to be processed
    post_selection : bool
        if true then only strings in logical zero are invalid.
        Strings outside the codespace are counted separately.
    simple : bool
        looks only at the parity of bits with exactly two non-zero columns in the parity matrix
    single : bool
        look at single bit only
    single_bit : int
        single bit to validate against

    Returns
    -------
    valid : int
        value if the bit string is valid
    invalid : int
        value if the bit string is invalid
    outside_codeword : int
        value if the bit string is outside the codespace

    Notes
    -----
    This code was originally designed to handle the codewords 
    in a list of lists, but will also work fine
    with a list of strings.  

    """
    if simple:
        if post_selection:
            raise Exception('simple and post selection algorithm are exclusive')
    valid = 0
    invalid = 0
    outside_codeword = 0
    #print('in compute_string_validity simple, codewords, reversed_data_string', simple, codewords, reversed_data_string)
    if post_selection:
            logical_zero = codewords
            logical_one = flip_code_words(codewords)
            if reversed_data_string in logical_zero:
                valid = value
            elif reversed_data_string in logical_one:
                invalid = value
            else:
                outside_codeword = outside_codeword + value
    elif simple:
        parity = '0'
        simple_parity_bits = calculate_simple_parity_bits()
        for bit_location in simple_parity_bits:
            if reversed_data_string[bit_location] == '1':
                #parity has changed
                if parity == '0':
                    parity = '1'
                else:
                    parity = '0'
        #print('reversed_data_string, parity, codewords', reversed_data_string, parity, codewords )
        if parity in codewords:
            valid = value
        else:
            invalid = value    
    elif single:
        if reversed_data_string[single_bit] in codewords:    
            valid = value
        else:
            invalid = value    
    else:
        if reversed_data_string in codewords:
            valid = value
        else:
            invalid = value

    return(valid, invalid, outside_codeword)

def calculate_simple_parity_bits():
    """returns a list of qubits with exactly two non zero rows in the parity matrix
    
    Returns
    -------
    simple_parity_bits : list
        A list of all qubits with exactly two non zero rows in the parity matrix
    """
    parity_matrix_totals = calculate_parity_matrix_totals()
    simple_parity_bits = []
    count = 0
    for items in parity_matrix_totals:
        if items == 2:
            simple_parity_bits.append(count)
        count = count + 1
    return(simple_parity_bits)

def find_individual_ancilla_values(ancilla_values, data_qubits, 
                                    ancilla_qubits, label_string = ''):
    """Returns the count of individual ancilla bit strings as a dictionary.

    Parameters
    ----------
    ancilla_values : dict
        holds the counts for each combination of ancilla bit strings.
    data_qubits : int
        number of data qubits used as an offset to calculate 
        the ancilla number
    ancilla_qubits : int
        number of ancilla qubits
    label_string : str
        first part of label 

    Returns
    -------
    individual_ancilla_values : dict
        dictionary containing the count of individual 
        ancilla bit string
    """

    #initialise dictionary to hold values
    individual_ancilla_values = {label_string + str(count): 0 
                                for count in range(data_qubits + 1, 
                                                    data_qubits + 1 + 
                                                    ancilla_qubits) }

    for ancilla, value in ancilla_values.items():
        for count in range(ancilla_qubits):
            bit = ancilla[count]
            if bit == '1':
                # note that order of Qiskit qubit order needs to be reversed to compare with the paper
                key = label_string + str(data_qubits + ancilla_qubits - count)
                old_count = individual_ancilla_values[key]
                new_count = old_count + value
                individual_ancilla_values[key] = new_count
    return(individual_ancilla_values)

def find_ancilla_values(counts, ancilla_qubits, ancilla_location = 0):
    """Returns a dictionary with a count of each possible ancilla bit string.

    Parameters
    ----------
    counts : dictionary
        counts for each possible output bit string
    anicilla_qubits : int
        number of ancilla qubits
    ancilla_location : int
        designates which bit string is relevant


    Returns
    -------
    ancilla_values : dict
        dictionary containing the count of each possible ancilla bit string

        """

    #build a list of all the possible ancilla in binary
    possible_ancilla_list = []
    format_string = '0' + str(ancilla_qubits) + 'b'
    for i in range(2 ** (ancilla_qubits)):
        possible_ancilla_value = format(i, format_string)
        possible_ancilla_list.append(possible_ancilla_value)

    #use the list to initialise a dictionary which hold the results by ancilla
    ancilla_values = {i:0 for i in possible_ancilla_list}  

    # loop through the results and summarise by ancilla
    for key, value in counts.items():
        #split out the ancilla part of key
        ancilla = key.split()[ancilla_location]
        old_count = ancilla_values[ancilla]
        new_count = old_count + value
        ancilla_values[ancilla] = new_count
    return(ancilla_values)

def strings_AND_bitwise(string1, string2):
    """Returns the bitwise AND of two equal length bit strings.

    Parameters
    ----------
    string1 : str
        First string
    string2 : str
        Second string
        
    Returns
    -------
    string_out : str
        bitwise AND of the two input strings
            
    """

    string_out = ''
    if len(string1) != len(string2):
        raise Exception('When taking the logical AND of two strings they must both have the same length')
    for count in range(len(string1)):
        i = (string1)[count]
        j = (string2)[count]
        k = '0'
        if i == '0':
            if j == '1':
                k = '1'
        if i == '1':
            if j == '0':
                k = '1'
        string_out = string_out + k
    return(string_out)

def string_ancilla_mask(location, length):
    """Returns a bit string with a 1 in a certain bit and the 0 elsewhere.

    Parameters
    ----------
    location : int
        location of the bit which should be set to '1' in the mask
    length : int
        length of string in the mask
        
    Returns
    -------

    string : str    
        ancilla bit mask string in required format    
    
    """

    if not isinstance(location, int):
        return Exception('Location of string must an integer when calculating ancilla mask')
    
    if not isinstance(length, int):
        return Exception('Length of string must an integer when calculating ancilla mask')

    if location < 1:
        return Exception('Location of string must be strictly positive when calculating ancilla mask')
    
    if length < 1:
        return Exception('String length must be greater than 1 when calculating ancilla mask')

    if length < location:
        return Exception('Location must be less than string length when calculating ancilla mask')

    string = '1'
    for i in range(length - 1):
        string = '0' + string

    for count in range(location - 1):
        new_string = string[1:7] + '0'
        string = new_string
    return(string)

def correct_qubit(data_in, ancilla, data_qubits):
    """Returns the corrected data bit string calculated from the ancilla settings.

    Parameters
    ----------
    data_in : str
        input data bit string
    ancilla : str
        three bit ancilla logical Z code
    data_qubits : int
        length of bit string
        
    Returns
    -------

    data_out : str
        corrected data bit string

    Notes
    -----
    The ancilla number calculation needs to take into account 
    that the ancilla bit string is reversed
    compared to numbering of the databits shown on the Qiskit diagrams.  
    This code corrects bit string errors only, not phase errors
        
    """
    data_out = ''
    
    if ancilla == '000':
        data_out = data_in
    else:
        bin_ancilla = string_reverse(ancilla)
        int_ancilla = int(bin_ancilla, 2)
        ancilla_mask = string_ancilla_mask(int_ancilla, data_qubits)
        data_out = strings_AND_bitwise(data_in, ancilla_mask)  
    return(data_out)

def flip_code_words(codewords_in):
    """Returns a list of codewords for the logical one from 
    the list of codewords for the logical zero
    by flipped each bit of the input codewords.

    Parameters
    ----------
    codewords : list
        logical codewords in seven bit Steane code data qubit 
        for the logical zero
    
    Returns
    -------
    Codewords_out : list
        bit flipped input codeword

    """

    codewords_out = []
    for items in codewords_in:
        new_string = ''
        for bit in items:
            if bit == '1':
                flipped_bit = '0'
            elif bit == '0':
                flipped_bit = '1'
            else:
                raise Exception('Not able to interpret bit in codewords')
            new_string = new_string + flipped_bit
        codewords_out.append(new_string)
    return(codewords_out)

def get_noise(p_meas, single_qubit_error, 
                two_qubit_error, single_qubit_gate_set, 
                two_qubit_gate_set, all = True, 
                noisy_qubit_list = [],
                decohere = False,
                dummy_gate_set = [],
                dummy_gate_error = 0
                ):
    """Returns a noise model

    Parameters
    ----------
    p_meas : float
        probability of X error on measurement
    single_qubit_error : float    
        probability of a depolarizing error on a single qubit gate
    two_qubit_error : float    
        probability of a depolarizing error on a two qubit gate
    single_qubit_gate_set : list
        list of all single qubit gate types relevant for noise
    two_qubit_gate_set : list
        list of all two qubit gate types relevant for noise
    all : bool
        apply two gate noise to all qubits
    noisy_qubit_list : list of list
        list of list of noisy qubits on which  errors are applied
    decohere : bool
        Add extra noise to represent de-coherence
    dummy_gate_set : list
        Set of dummy gates on which the de-coherence error is applied.  Normally ['id'].
    dummy_gate_error : flot
        error to apply to dummy gate which is set up to model de-coherence at certain stages in the circuit. 

    Returns
    -------
    noise_model : dict
        noise model to be used

    Notes
    -----
    Can apply noise selectively to qubits in noisy_qubit_list.  This is a list of lists.
    """
    error_meas = pauli_error([('X', p_meas), ('I', 1 - p_meas)])
    error_gate1 = depolarizing_error(single_qubit_error, 1)
    error_gate2 = depolarizing_error(two_qubit_error, 1)
    error_gate3 = error_gate2.tensor(error_gate2)
    if decohere:
        if 'id' in single_qubit_gate_set:
            raise ValueError('Do not include gate id in the single_qubit_gate_set as used for decoherent errors')
        error_decohere = depolarizing_error(dummy_gate_error, 1)
    noise_model = NoiseModel()
    if all:
        if noisy_qubit_list != []:
            raise ValueError('Errors are applied to all qubits but a list of qubits with errors is given')    
        noise_model.add_all_qubit_quantum_error(error_meas, 'measure')      
        # measurement error is applied to measurements
        noise_model.add_all_qubit_quantum_error(error_gate1, 
                                                single_qubit_gate_set)  
        # single qubit gate errors
        noise_model.add_all_qubit_quantum_error(error_gate3,
                                                 two_qubit_gate_set) 
        # two qubit gate error is applied to two qubit gates
        if decohere:
            noise_model.add_all_qubit_quantum_error(error_decohere,
                                                    dummy_gate_set) 
        # decoherence error is applied to dummy gates
    else:
        if noisy_qubit_list == []:
            raise ValueError('A list of qubits must be supplied if errors are not to be applied to all qubits')
        #read through list of list of error gates
        for gate_list in noisy_qubit_list:
            for gate_index1 in gate_list:
                noise_model.add_quantum_error(error_meas, 'measure', 
                                                [gate_index1]
                                                ) 
                # measurement error is applied to measurements
                noise_model.add_quantum_error(error_gate1, 
                                                single_qubit_gate_set, 
                                                [gate_index1]
                                                )  
                if decohere:
                    noise_model.add_quantum_error(error_decohere ,
                                                    dummy_gate_set, 
                                                    [gate_index1]
                                                    ) 
        # decoherence error is applied to dummy gates
                # single qubit gate errors
                for gate_index2 in gate_list:
                    if gate_index1 != gate_index2:
                        noise_model.add_quantum_error(error_gate3, 
                                                    two_qubit_gate_set, 
                                                    [gate_index1,
                                                     gate_index2]
                                                     )    
    return noise_model   

def mean_of_list(list_in):
    """Returns the mean of a list

    Parameters
    ----------

    list_in : list
        data for analysis

    Returns
    -------
    mean : float
        result of calculation
        """
    mean = sum(list_in) / len(list_in)
    return(mean)

def calculate_standard_error(list_in):
    """ Calculates the standard error of a list of numbers

    Parameters
    ----------
    list_in : list
        data for analysis

    Returns
    -------
    standard_deviation : float
        standard deviation estimated from sample
    standard_error : float
        standard error estimated from sample
        result of calculation
    """
    
    if len(list_in) > 1:
        standard_deviation = stdev(list_in)
        standard_error = standard_deviation / sqrt(len(list_in))
    elif len(list_in) == 1:
        standard_deviation = 0
        standard_error = 0
        print('Unable to carry out standard error calcuation with one point. ')  
        print('Standard error of 0 used.')
    else:
        raise ValueError('f The number of iterations must be positive {iterations} used')
    return(standard_deviation, standard_error)

def convert_codewords(codewords):
    """ Changes the codewords list of lists to a list of strings

    Parameters
    ----------
    codewords : list
        allowed codewords for logical zero

    Returns
    -------
    list_of_strings : list
        a list of strings


    Notes
    -----
    No longer needed at present as codeword is a list of strings 
    but retained in case needed in future.
    """

    list_of_strings = []
    for lists in codewords:
        new_string = ''
        for item in lists:
            new_string = new_string + str(item)
        list_of_strings.append(new_string)

    return(list_of_strings)

def summarise_logical_counts(counts, logical_zero_strings, logical_one_strings, 
                            data1_location, data2_location):
    """Simplifies bit strings for logical operations 
    to show each qubit as 0, 1, or 2 instead of the full bit string.
        0.  means qubit is the logical zero
        1.  means qubit is the logical one
        2.  means qubit is outside code space

    Parameters
    ----------
    counts : dict
        results of computation
    logical_zero_strings : list    
        list of strings in logical zero
    logical_one_strings : list     
        list of strings in logical zero
    data1_location : int
        where in the counts bit string data1 is held
    data2_location : int
        where in the counts bit string data2 is held
    
    Returns
    -------
    new_counts : dict
        simplified results
    """
    # convert list of list to list of strings
    #logical_zero_strings = convert_codewords(logical_zero)
    #logical_one_strings = convert_codewords(logical_one)

    #set up dictionary to hold answer
    new_counts = {str(i) + str(j):0 for i in range(3) for j in range(3)}
    for key, value in counts.items():
        #split out the data parts of key
        data1 = key.split()[data1_location]
        data2 = key.split()[data2_location]
        #need to reverse the string from qiskit format
        reverse1 = string_reverse(data1)
        reverse2 = string_reverse(data2)
        new_data1 = look_up_data(reverse1, logical_zero_strings, logical_one_strings)
        new_data2 = look_up_data(reverse2, logical_zero_strings, logical_one_strings)
        new_key = new_data1 + new_data2
        if new_counts.get(new_key) == None: 
             new_counts.update({new_key: value})
        else:
            new_counts[new_key] = new_counts[new_key] + value
    return(new_counts)

def look_up_data(input_string, logical_zero, logical_one):
    """Looks up the input data to determine if the string is a logical one,
    logical zero, or outside the code base.

    Parameters
    ----------
    input_string : str
        data for analysis
    logical_zero : list    
        list of strings representing a logical zero
    logical_one : str     
        list of strings representing a logical one
    
    Returns
    -------
    output_string : str
        result of look-up"""

    if input_string in logical_zero:
        output_string = '0'
    elif input_string in logical_one:
        output_string = '1'
    else:
        output_string = 'E'
    return(output_string)

def print_time():
    """Prints current time"""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    return

def validate_integer(number):
    """Checks if a number is an integer.

    Parameters
    ----------
    number: int
        number to be validated
        """
    if type(number) != int:
        raise ValueError(f'The number {number} entered is not an integer')

def process_FT_results(counts, codewords, data_meas_strings = ['0'], 
                        anc_zero = '0', anc_one = '1',
                        verbose = False, data_qubits = 7,  
                        ancilla_start = 0, data_meas_start = 0, data_start = 0,
                        ancilla_types = 2, ancilla_qubits = 0, ancilla_meas_repeats = 1,
                        data_meas_qubits = 0, data_meas_repeats = 0,
                        post_selection = False, simple = False,
                        ):

    """Process results from fault tolerant processing.

    Parameters
    ----------
    counts : dictionary
        results for analysis
    codewords : list
        list of valid data codewords
    data_meas_strings: string
        allowed strings for the data measurement bits
    anc_zero : string
        allowed strings for the ancilla zero
    anc_one : string
        allowed strings for the ancilla one
    verbose : bool
        if true enables printing
    data_qubits : int
        Length of data bit string.  Usually seven
    ancilla_start : int
        starting place for ancilla (if any)
    data_meas_start : int
        starting place for data measurement qubits (if any)
    data_start : int
        starting place for data string
    ancilla_types : int
        number of different ancilla types.  Normally 2 (X and Z) or 0
    ancilla_qubits : int
        number of strings for each ancilla qubits.  Normally 0, 1 or 3
    ancilla_meas_repeats : int
        number of times ancilla measurements are repeated.  Normally 3 or 1
    data_meas_qubits : int
        number of distinct data measurement qubits.  Normally 7, 1 or 0
    data_meas_repeats: int
        number of times data measurements are repeated.  Normally 3 or 1.
    post_select: bool
        if true then only strings in logical zero are invalid
    simple : book
        if true then simple decoding based on three bits shall be used.

    Returns
    -------
    error_rate : float
        error rate calculated
    rejected : int
        strings rejected for validation
    accepted : int
        strings accepted for validation
    valid : int
        strings validated and found to be in the code space
    invalid : int
        strings validated and found to not be in the code space

    Notes
    -----
    This function takes the output string, splits it, and determines if it passes
    data and ancilla checks.  If so the data keyword is validated.
    """

    anc_meas_strings = [anc_zero, anc_one]
    validate_integer(ancilla_start)
    validate_integer(data_meas_start)
    validate_integer(data_start)
    validate_integer(ancilla_types)
    validate_integer(ancilla_qubits)
    validate_integer(ancilla_meas_repeats)
    validate_integer(data_meas_qubits)
    validate_integer(data_meas_repeats)  
    total_keys = ancilla_types * ancilla_qubits * ancilla_meas_repeats
    total_keys = total_keys + (data_meas_qubits * data_meas_repeats) + 1   
    count_valid = 0
    count_invalid = 0
    count_outside_codeword = 0
    ancilla_rejected = 0
    ancilla_accepted = 0
    data_rejected = 0
    data_accepted = 0
    rejected = 0
    accepted = 0
    for string, value in counts.items():
        qubit_strings = []
        data_syndrome_strings = []
        data_OK = False
        for i in range(total_keys):
            qubit_strings.append(string.split()[i])
        data_string = qubit_strings[data_start]
        for i in range(data_meas_start, data_meas_start + data_meas_repeats):
        #need to reverse strings because Qiskit reverses them
            data_syndrome_strings.append(string_reverse(qubit_strings[i]))  
        if data_meas_repeats == 3:
                if data_syndrome_strings[2] in data_meas_strings:
                    if data_syndrome_strings[1] in data_meas_strings:
                        if data_syndrome_strings[0] in data_meas_strings:
                            data_OK = True
        elif data_meas_repeats == 0:
            data_OK = True
        else:
            raise Exception('At present only 3 or zero data measurements are coded for')
        if data_OK:
            data_accepted = data_accepted + value
            if ancilla_qubits == 0:
                #no ancilla
                ancilla_accepted = data_accepted
                ancilla_rejected = 0
                ancilla_OK = True
                corrected_data_string = data_string
            elif ancilla_qubits == 1:
                #simple case without fault tolerance.  No check on ancilla possible
                ancilla_OK = True
                ancilla_accepted = data_accepted
                ancilla_rejected = 0
                if ancilla_meas_repeats != 1: 
                    raise Exception('can not handle multiple measurements on one ancilla qubit')
                ancilla = qubit_strings[ancilla_start]
                corrected_data_string = correct_qubit(data_string, ancilla, data_qubits)    
            elif ancilla_qubits == 3:
                #complex case with fault tolerance
                count_ancilla_OK = 0
                X = ['' for i in range(ancilla_qubits)]
                for i in range(ancilla_types):
                    for j in range(ancilla_meas_repeats):
                        first = i * (ancilla_qubits * ancilla_meas_repeats) + j * ancilla_meas_repeats
                        second = first + 1
                        third = second + 1
                        if qubit_strings[third] == qubit_strings[second]:
                            if qubit_strings[second] == qubit_strings[first]:
                                if qubit_strings[first] in anc_meas_strings:
                                    count_ancilla_OK = count_ancilla_OK + 1
                                    if i == 0:
                                        #only interested in X values
                                        if qubit_strings[first] in anc_zero:
                                            X[j] = '0'
                                        elif qubit_strings[first] in anc_one:
                                            X[j] = '1'
                                        else:
                                            raise Exception('Error in processing strings for i, j, k = {i}, {j}, {k}')
                if count_ancilla_OK == ancilla_qubits * ancilla_types:
                    ancilla_OK = True
                    ancilla_accepted = ancilla_accepted + value
                    #always first three ancilla with Steane code
                    ancilla = X[0] + X[1] + X[2]
                    corrected_data_string = correct_qubit(data_string, ancilla, data_qubits)
                else:
                    ancilla_OK = False
                    ancilla_rejected = ancilla_rejected + value
            else:
                raise Exception('Can only process ancilla strings of 0, 1 or 3 qubits')
            if ancilla_OK:
                #need to reverse string because of Qisit convention
                reversed_data_string = string_reverse(corrected_data_string)
                #print('corrected_data_string, reversed_data_string', corrected_data_string, reversed_data_string)
                valid, invalid, outside_codeword = compute_string_validity(value, 
                                                                        codewords, 
                                                                        reversed_data_string, 
                                                                        post_selection = post_selection, 
                                                                        simple = simple, 
                                                                        )
                #print('value, codewords, reversed_data_string, simple',value, codewords, reversed_data_string, simple)
                #print('valid, invalid, count_outside_codeword',valid, invalid, count_outside_codeword, )
                count_valid = count_valid + valid
                count_invalid = count_invalid + invalid
                count_outside_codeword = count_outside_codeword + outside_codeword
                
                
                #if post_selection:
                #    logical_zero = codewords
                #    logical_one = flip_code_words(codewords)  
                #    if string_reverse(corrected_data_string) in logical_zero:
                #        valid = valid + count
                #    elif string_reverse(corrected_data_string) in logical_one:
                #        invalid = invalid + count
                #    else:
                #        outside_codewords = outside_codewords + count
                #else:
                #    if string_reverse(corrected_data_string) in codewords:
                #        valid = valid + count
                #    else:
                #        invalid = invalid + count
        else:
            data_rejected = data_rejected + value

    if ancilla_accepted != 0:
        # calculate on ancilla_accepted because this always holds the amounts to be validated
        error_rate = count_invalid / ancilla_accepted
    else:   
        error_rate = 0
        print('Error rate not defined as no strings accepted')
    rejected = data_rejected + ancilla_rejected
    accepted = ancilla_accepted 
    if verbose:
        print(f'At the data validation stage')        
        print(f'There are {data_rejected} strings rejected and {data_accepted} strings submitted for processing')
        print(f'Making {data_rejected + data_accepted} in total submitted for data processing')
        print()
        print(f'At the ancilla validation stage')   
        print(f'There are {ancilla_rejected} strings rejected and {ancilla_accepted} strings submitted for validation')
        print(f'Making {ancilla_rejected + ancilla_accepted} in total submitted to check against ancilla') 
        print()
        print(f'Of these {ancilla_accepted} strings validated there are {count_valid} valid strings and {count_invalid} invalid_strings')
        if post_selection:
            print(f'There were {count_outside_codeword} strings that were neither logical one or logical zero')
        print(f'The error rate is {error_rate:.4f}')
    return(error_rate, rejected, accepted, count_valid, count_invalid)

def get_parity_check_matrix():
    """Stores the parity matrix in one place"""
    parity_check_matrix =   ['0001111',
                            '0110011',
                            '1010101'
                            ]
    return(parity_check_matrix)

def get_codewords():
    """Stores the codewords in one place"""
    codewords =['0000000',
                '1010101',
                '0110011',
                '1100110',
                '0001111',
                '1011010',
                '0111100',
                '1101001'
                ]
    return(codewords)

def calculate_parity_matrix_totals():
    """calculates the number of items in each row of the parity matrix"""
    parity_check_matrix = get_parity_check_matrix()
    n = len(parity_check_matrix[0])
    parity_matrix_totals = [ 0 for x in range(n)] # define an empty list 
    #ready to work out parity_matrix_totals
    #calculate the number of non-zero entries in each row of the parity matrix and store
    for parity_string in parity_check_matrix :
        for index in range(n):
            parity_matrix_totals[index] = parity_matrix_totals[index] + int(parity_string[index])
    return(parity_matrix_totals)