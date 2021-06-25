#helper_functions.py

from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import pauli_error, depolarizing_error
from statistics import stdev
from math import sqrt

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

def count_valid_output_strings(counts, codewords, data_position):
    """Finds the number of valid and invalid output bit strings in a given position in a dictionary representing
    the counts for each output bit string.

    Parameters
    ----------
    counts : dictionary
        holds the observed populations for each combination of qubit
    codewords : list
        holds allowed codewords 
    data_position : int 
        position of the data string

    Returns
    ----------
    Count_valid : int
        Number of valid bit strings
    Count_invalid : int
        Number of invalid bit strings

    """
    count_valid = 0
    count_invalid = 0
    for key, value in counts.items():
        #split out data part of key
        data = key.split()[data_position]
        #need to reverse the data string showing the relevant qubits as 
        #the codewords and the data have a different format 
        reversed_data_string = string_reverse(data)
        flag = False
        for items in codewords:
            #turn the codeword list into a string
            codeword_string = ''.join(map(str, items))
            if reversed_data_string == codeword_string:
                flag = True
        if flag == True:
            count_valid = count_valid + value
        else:
            count_invalid = count_invalid + value
    return(count_valid, count_invalid)


def find_individual_ancilla_values(ancilla_values, data_qubits, ancilla_qubits, label_string = ''):
    """Returns the count of individual ancilla bit strings as a dictionary.

    Parameters
    ----------
    ancilla_values : dict
        holds the counts for each combination of ancilla bit strings.
    data_qubits : int
        number of data qubits used as an offset to calculate the ancilla number
    ancilla_qubits : int
        number of ancilla qubits
    label_string : str
        first part of label 

    Returns
    -------
    individual_ancilla_values : dict
        dictionary containing the count of individual ancilla bit string
    """

    #initialise dictionary to hold values
    individual_ancilla_values = {label_string + str(count): 0 for count in range(data_qubits + 1, data_qubits + 1 + ancilla_qubits) }

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
       # print(i, j, k)
        string_out = string_out + k
    return(string_out)

def string_ancilla_mask(location, length):
    """Returns a bit string with a 1 in a certain bit and the 0 elsewhere.

    Parameters
    ----------
    location : int
        bit which should be 1 
    length : int
        length of string
        
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
    #print(count)
        new_string = string[1:7] + '0'
        string = new_string
    #print(new_string)

    return(string)

def correct_qubit(data_in, ancilla, data_qubits):
    """Returns the corrected data bit string calculated from the ancilla settings.

    Parameters
    ----------
    data : str
        input data bit string
    ancilla : str
        three bit ancilla X code
    data_qubits : int
        length of bit string
        
    Returns
    -------

    data_out : str
        corrected data bit string

    Notes
    -----
    The ancilla number calculation needs to take into account that the ancilla bit string is reversed
    compared to numbering of the databits shown on the qiskit diagrams
        
    """

    if ancilla == '000':
        data_out = data_in
    else:
        bin_ancilla = string_reverse(ancilla)
        dec_ancilla = int(bin_ancilla, 2)
        ancilla_mask = string_ancilla_mask(dec_ancilla, data_qubits)
        data_out = strings_AND_bitwise(data_in, ancilla_mask)  

    return(data_out)

def flip_code_words(codewords_in):
    """Returns a list of codewords for the logical one from the list of codewords for the logical zero
    by flipped each bit of the input codewords.

    Parameters
    ----------
    codewords : list
        logical codewords in seven bit Steane code data qubit for the logical zero
    
    Returns
    -------
    Codewords_out : list
        bit flipped input codeword

    """

    codewords_out = []
    for items in codewords_in:
        new_list = []
        for bit in items:
            if bit == 1:
                flipped_bit = 0
            elif bit == 0:
                flipped_bit = 1
            else:
                raise Exception('Not able to interpret bit in codewords')
            new_list.append(flipped_bit)
        codewords_out.append(new_list)
    return(codewords_out)

def get_noise(p_meas, single_qubit_error, two_qubit_error, single_qubit_gate_set, two__qubit_gate_set):
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
        list of all single qubit gates relevant for noise
    two__qubit_gate_set: list
        list of all two qubit gates relevant for noise.
    
    Returns
    -------
    noise_model : dict
        noise model to be used

    """
    error_meas = pauli_error([('X', p_meas), ('I', 1 - p_meas)])
    error_gate1 = depolarizing_error(single_qubit_error, 1)
    error_gate2 = depolarizing_error(two_qubit_error, 1)
    error_gate3 = error_gate2.tensor(error_gate2)

    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(error_meas, 'measure') # measurement error is applied to measurements
    noise_model.add_all_qubit_quantum_error(error_gate1, single_qubit_gate_set)  # single qubit gate errors
    noise_model.add_all_qubit_quantum_error(error_gate3, two__qubit_gate_set) # two qubit gate error is applied to two qubit gates
    
    return noise_model   

def summarise_logical_counts(counts, logical_zero, logical_one, data1_location, data2_location):
    """Summarises logical operation counts 

    Parameters
    ----------
    counts : dict
        results of computation
    logical_zero : str    
        string for the output after decoding representing a logical zero
    logical_one : str     
        string for the output after decoding representing a logical one
    data1_location : int
        where in the counts bit string data1 is held
    data2_location : int
        where in the counts bit string data2 is held
    
    Returns
    -------
    new_counts : dict
        simplified results
        
    Returns
    -------
    A string '2' is used to represent bits that are outside the code base  
    """

    #set up dictionary for answer
    new_counts = {str(i) + str(j):0 for i in range(3) for j in range(3)}
    for key, value in counts.items():
        #split out the data parts of key
        data1 = key.split()[data1_location]
        data2 = key.split()[data2_location]
        new_data1 = look_up_data(data1, logical_zero, logical_one)
        new_data2 = look_up_data(data2, logical_zero, logical_one)
        new_key = new_data1 + new_data2
        new_counts[new_key] = new_counts[new_key] + value
    return(new_counts)

def look_up_data(data_in, logical_zero, logical_one):
    """Looks up the input data to determine if the string is a logical one,
    logical zero, or outside the code base.

    Parameters
    ----------
    data_in : str
        data for analysis
    logical_zero : str    
        string for the output after decoding representing a logical zero
    logical_one : str     
        string for the output after decoding representing a logical one
    
    Returns
    -------
    new_data : str
        result of look-up"""

    if data_in == logical_zero:
        new_data = '0'
    elif data_in == logical_one:
        new_data = '1'
    else:
    #outside code range
        new_data = '2'
    return(new_data)

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
        print('Unable to carry out standard error calcuation with one point')
    else:
        raise ValueError('f The number of iterations must be positive {iterations} used')
    return(standard_deviation, standard_error)


            
        


