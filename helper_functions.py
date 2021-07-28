#helper_functions.py

from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import pauli_error, depolarizing_error
from statistics import stdev
from math import sqrt
from datetime import datetime

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

def count_valid_output_strings(counts, codewords, data_location = 0):
    """Finds the number of valid and invalid output bit strings in a given location in a dictionary representing
    the counts for each output bit string.

    Parameters
    ----------
    counts : dictionary
        holds the observed populations for each 
        combination of qubit
    codewords : list
        holds allowed codewords 
    data_location : int 
        location of the data string

    Returns
    -------
    Count_valid : int
        Number of valid bit strings
    Count_invalid : in
        Number of invalid bit strings

    Notes
    -----
    This code was originally designed to handle the codewords 
    in a list of lists, but will also work fine
    with a list of strings.

    """
    count_valid = 0
    count_invalid = 0
    for key, value in counts.items():
        #split out data part of key
        if data_location == 0:
            data = key
        else:
            data = key.split()[data_location]
        #need to reverse the data string showing the relevant qubits as 
        #the codewords and the data have a different format 
        reversed_data_string = string_reverse(data)
        flag = False
        for items in codewords:
            #turn the codeword list into a string if presented as a list
            #not really needed any more but kept
            codeword_string = ''.join(map(str, items))
            if reversed_data_string == codeword_string:
                flag = True
        if flag == True:
            count_valid = count_valid + value
        else:
            count_invalid = count_invalid + value
    return(count_valid, count_invalid)


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
        new_string = string[1:7] + '0'
        string = new_string
    return(string)

def correct_qubit(data_in, ancilla, data_qubits):
    """Returns the corrected data bit string calculated from the ancilla settings.

    Parameters
    ----------
    data : str
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
        dec_ancilla = int(bin_ancilla, 2)
        ancilla_mask = string_ancilla_mask(dec_ancilla, data_qubits)
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
                noisy_qubit_list = []
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

def summarise_logical_counts(counts, logical_zero, logical_one, 
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
    logical_zero : list    
        list of list of items in logical zero
    logical_one : list     
        list of list of items in logical zero
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
    logical_zero_strings = convert_codewords(logical_zero)
    logical_one_strings = convert_codewords(logical_one)

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

    #outside code range unless found
    output_string = '2'
    for string in logical_zero:
        if string == input_string:
            output_string = '0'
    for string in logical_one:
        if string == input_string:
            output_string = '1'
    return(output_string)

def print_time():
    """function to print time    now = datetime.now()"""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    return

def validate_integer(number):
    """Function to check if a number is an integer.

    Parameters
    ----------
    number: int
        number to be validated
        """
    if type(number) != int:
        raise ValueError(f'The number {number} entered is not an integer')

def process_FT_results(counts, codewords, scheme):
    """Process results from fault tolerant processing.

    Parameters
    ----------
    counts : dictionary
        results for analysis
    codewords : list
        list of valid codewords
    scheme : string    
        fault tolerance scheme for Goto.
        B = repeated data.   
        C = one extra qubit
        N = non fault tolerant  
        S = single qubit
    
    Returns
    -------
    error_rate : float
        error rate calculated
    rejected : int
        strings rejected
    accepted : int
        strings accepted for further processing
    valid : int
        accepted strings in the code space
    invalid : int
        rejected strings not in the code space
    """
    valid = 0
    invalid = 0
    rejected = 0
    accepted = 0
    for string, count in counts.items():
        processed = False
        #need to reverse strings because Qiskit reverses them
        if scheme in ['B', 'C']: #Goto fault tolerance scheme B or C
            string0 = string_reverse(string.split()[3])
            string1 = string_reverse(string.split()[2])
            string2 = string_reverse(string.split()[1])
            string3 = string_reverse(string.split()[0])
        elif scheme =='S': #single qubit
            string0 = string
        elif scheme == 'N': #non fault tolerant
            string0 = string_reverse(string)
        else:
            raise ValueError(f'Only scheme B, C, N and S are supported.  Scheme {scheme} is not recognised')
        if scheme == 'B': 
            if string1 in codewords:
                if string2 in codewords:  
                    if string3 in codewords:
                        processed = True  #processed in scheme B
        elif scheme == 'C':
            if string1 == string2:
                if string2 == string3:  
                    if string1 == '0':
                        processed = True  #processed in scheme C  
        elif scheme in ['S','N']:
            processed = True  #no rejection processed in schemes S and N
        else:
            raise ValueError(f'Only scheme B, C, N and S are supported.  Scheme {scheme} is not recognised')
        if processed:
            accepted = accepted + count
            if string0 in codewords:  #would be reported as valid
                valid = valid + count
            else:
                invalid = invalid + count
        else:
            rejected = rejected + count
    if accepted != 0:
        error_rate = invalid / accepted
    else:   
        error_rate = 0
        print('Error rate not defined as no strings accepted')
    return(error_rate, rejected, accepted, valid, invalid)

    

